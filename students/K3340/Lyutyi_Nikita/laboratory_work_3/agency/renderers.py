"""JSON renderer with an explicit UTF-8 charset for older Windows clients."""

from rest_framework.renderers import JSONRenderer


class UTF8JSONRenderer(JSONRenderer):
    charset = "utf-8"
