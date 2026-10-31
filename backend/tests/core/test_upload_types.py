"""Pictures under /uploads go out with their own content type, not text/plain (the slim image has no /etc/mime.types)."""
import mimetypes

from app.core import routes


def test_webp_pictures_are_served_as_images_even_where_the_system_does_not_know_webp(monkeypatch):
    bare = mimetypes.MimeTypes(filenames=())
    bare.types_map = ({}, {})
    bare.types_map_inv = ({}, {})
    monkeypatch.setattr(mimetypes, "_db", bare)
    monkeypatch.setattr(mimetypes, "inited", True)
    assert mimetypes.guess_type("uploads/project_maps/p1.webp")[0] is None
    routes.register_picture_types()
    assert mimetypes.guess_type("uploads/project_maps/p1.webp")[0] == "image/webp"
    assert mimetypes.guess_type("uploads/builder_logos/lodha.png")[0] == "image/png"
