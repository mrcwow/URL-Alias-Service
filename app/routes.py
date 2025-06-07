from flask import redirect, request
from flask_restx import Namespace, Resource, fields, abort, reqparse
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta
from . import db, SERVICE_URL
from .models import URL, Click
from .auth import require_auth
from .utils import generate_url

api = Namespace("service", description="URL Alias Service")

parser = reqparse.RequestParser()
parser.add_argument("page", type=int, required=False, default=1, help="Page number")
parser.add_argument("per_page", type=int, required=False, default=10, help="Items per page")
parser.add_argument("is_active", type=str, required=False, choices=("true", "1", "yes"), help="Filter by active URLs, without param all items")

url_model = api.model("URL", {
    "url": fields.String(readonly=True),
    "orig_url": fields.String(required=True),
    "create_time": fields.DateTime(readonly=True),
    "expire_time": fields.DateTime(readonly=True),
    "is_active": fields.Boolean(readonly=True)
})

stats_model = api.model("Stats", {
    "url": fields.String(readonly=True),
    "orig_url": fields.String(readonly=True),
    "last_hour_clicks": fields.Integer(readonly=True),
    "last_day_clicks": fields.Integer(readonly=True)
})

@api.route("/")
class URLList(Resource):
    @api.expect(parser)
    @require_auth
    @api.doc(security="basicAuth")
    def get(self):
        args = parser.parse_args()
        page = args.get("page")
        per_page = args.get("per_page")
        is_active_raw = args.get("is_active")
        is_active = (
            is_active_raw.lower() in ["true", "1", "yes"]
            if is_active_raw is not None else None
        )

        query = URL.query
        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        try:
            pagination = query.paginate(page=page, per_page=per_page)
        except SQLAlchemyError as e:
            abort(500, f"Database error: {str(e)}")
            return
        
        return {
            "items": [api.marshal(url, url_model) for url in pagination.items],
            "total_items": pagination.total,
            "page": pagination.page,
            "total_pages": pagination.pages
        }

    @api.expect(url_model)
    @api.marshal_with(url_model)
    @require_auth
    @api.doc(security="basicAuth")
    def post(self):
        data = api.payload
        url = ""
        
        try:
            url = generate_url(data["orig_url"])
        except SQLAlchemyError as e:
            abort(500, f"Database error: {str(e)}")
        except ValueError as e:
            abort(400, str(e))
        
        url = URL(
            orig_url=data["orig_url"],
            url=url
        )
        
        try:
            db.session.add(url)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, f"Database error: {str(e)}")
            
        return url

@api.route("/<short_code>")
class URLRedirect(Resource):
    def get(self, short_code):
        try:
            url = URL.query.filter_by(url=SERVICE_URL+short_code).first()
        except SQLAlchemyError as e:
            abort(500, f"Database error: {str(e)}")
            return
        
        if not url:
            abort(404, "URL not found")
        if url.expire_time < datetime.now(timezone.utc).replace(tzinfo=None):
            url.is_active = False
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
            abort(404, "URL expired")
        if not url.is_active:
            abort(404, "URL deactivated")
        
        click = Click(url_id=url.id)
        try:
            db.session.add(click)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, f"Database error: {str(e)}")
        
        return redirect(url.orig_url)

@api.route("/<short_code>/deactivate")
class URLDeactivate(Resource):
    @require_auth
    @api.doc(security="basicAuth")
    def put(self, short_code):
        try:
            url = URL.query.filter_by(url=SERVICE_URL+short_code).first()
        except SQLAlchemyError as e:
            abort(500, f"Database error: {str(e)}")
            return
        
        if not url:
            abort(404, "URL not found")
            
        url.is_active = False
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, f"Database error: {str(e)}")
            
        return {"message": "URL deactivated"}

@api.route("/stats")
class URLStats(Resource):
    @api.marshal_with(stats_model, as_list=True)
    @require_auth
    @api.doc(security="basicAuth")
    def get(self):
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        
        stats = {}
        
        try:
            stats = db.session.query(
                URL.url,
                URL.orig_url,
                db.func.sum(
                    db.case(
                        (Click.click_time >= one_hour_ago, 1),
                        else_=0
                    )
                ).label("last_hour_clicks"),
                db.func.sum(
                    db.case(
                        (Click.click_time >= one_day_ago, 1),
                        else_=0
                    )
                ).label("last_day_clicks")
            ).outerjoin(Click).group_by(URL.id).order_by(db.desc("last_day_clicks")).all()
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, f"Database error: {str(e)}")
        
        return [{
            "url": stat.url,
            "orig_url": stat.orig_url,
            "last_hour_clicks": stat.last_hour_clicks,
            "last_day_clicks": stat.last_day_clicks
        } for stat in stats]