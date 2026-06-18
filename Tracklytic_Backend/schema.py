from drf_spectacular.openapi import AutoSchema


class TracklyticAutoSchema(AutoSchema):
    def _get_tags(self):
        tags = super()._get_tags()
        if tags and tags[0] == "auth":
            return ["Authentication"]
        return tags
