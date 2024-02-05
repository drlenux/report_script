import csv
from io import StringIO
from starlette.responses import StreamingResponse


def json_to_csv(json: dict):
    def iter_csv(data):
        pseudo_buffer = StringIO()
        writer = csv.writer(pseudo_buffer)
        writer.writerow(data[0].keys())

        for item in data:
            writer.writerow(item.values())
            yield pseudo_buffer.getvalue()
            pseudo_buffer.seek(0)
            pseudo_buffer.truncate(0)

    response = StreamingResponse(iter_csv(json), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response
