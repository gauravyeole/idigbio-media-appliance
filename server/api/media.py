import os

from flask import Blueprint, request, g, jsonify
from flask_restful import Api, Resource
from models import Media

media_api = Api(Blueprint("media_api", __name__))


def format_status_date(media):
    status_date = None
    if media.status_date is not None:
        status_date = media.status_date.isoformat()

    return status_date


@media_api.resource("/media")
class MediaAPI(Resource):

    @staticmethod
    def get():
        return {
            "count": Media.query.count(),
            "media": [
                {
                    "id": media.id,
                    "path": media.path,
                    "media_type": media.media_type,
                    "mime": media.mime,
                    "file_reference": media.file_reference,
                    "image_hash": media.image_hash,
                    "status": media.status,
                    "status_date": format_status_date(media),
                    "status_detail": media.status_detail
                } for media in Media.query[:100]
            ]
        }

    @staticmethod
    def post():
        from app import db

        if g.appuser is None:
            j = jsonify({"error": "Not Authorized"})
            j.status_code = 401
            return j

        b = request.get_json()

        media = Media()
        media.path = os.path.abspath(b["path"])
        media.file_reference = b["file_reference"]
        media.appuser = g.appuser

        if "media_type" in b:
            media.media_type = b["media_type"]

        if "mime" in b:
            media.mime = b["mime"]

        if "image_hash" in b:
            media.image_hash = b["image_hash"]

        db.session.add(media)
        db.session.commit()

        return {
            "id": media.id,
            "path": media.path,
            "media_type": media.media_type,
            "mime": media.mime,
            "file_reference": media.file_reference,
            "image_hash": media.image_hash,
            "status": media.status,
            "status_date": format_status_date(media),
            "status_detail": media.status_detail
        }


@media_api.resource("/media/<int:media_id>")
class MediaItemAPI(Resource):

    @staticmethod
    def get(media_id):
        from app import db

        media = Media.query.get_or_404(media_id)

        return {
            "id": media.id,
            "path": media.path,
            "media_type": media.media_type,
            "mime": media.mime,
            "file_reference": media.file_reference,
            "image_hash": media.image_hash,
            "status": media.status,
            "status_date": format_status_date(media),
            "status_detail": media.status_detail
        }


@media_api.resource("/media/status")
class MediaStatusAPI(Resource):

    @staticmethod
    def get():
        from app import db

        statuses = db.session.query(db.func.count(Media.status).label(
            "c"), Media.status).group_by(Media.status).all()

        resp_d = {
            "count": Media.query.count()
        }

        for m in statuses:
            if m.status is None:
                resp_d["NULL"] = m.c
            else:
                resp_d[m.status] = m.c

        return resp_d
