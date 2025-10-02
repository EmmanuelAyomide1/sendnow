from drf_yasg import openapi


def object_of_string_schema(parameter):
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            parameter: openapi.Schema(type=openapi.TYPE_STRING)
        }
    )


def list_of_strings_schema(parameter):
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            parameter: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    )
