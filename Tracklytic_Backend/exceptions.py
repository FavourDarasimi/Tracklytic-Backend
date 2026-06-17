from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data

        if isinstance(detail, dict):
            first_error = None
            for value in detail.values():
                if isinstance(value, list) and value:
                    first_error = str(value[0])
                    break
                elif isinstance(value, str):
                    first_error = value
                    break
            message = first_error or "An error occurred"
        elif isinstance(detail, list) and detail:
            message = str(detail[0])
        else:
            message = str(detail) if detail else "An error occurred"

        response.data = {
            "status": "error",
            "message": message,
        }

    return response
