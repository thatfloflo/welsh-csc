import click
import urllib.request
import urllib.error
from typing import Container, Final


HTTP_STATUS_CODES: Final[dict[int, str]] = {
    100: "Continue",
    101: "Switching protocols",
    102: "Processing",
    103: "Early Hints",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Switch Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a Teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}


class URLParamType(click.ParamType):
    name = "URL"

    def __init__(
        self,
        permitted_schemes: Container[str] | None = None,
        default_scheme: str = "http",
        ignore_http_errors: bool = True
    ) -> None:
        super().__init__()
        self.permitted_schemes = permitted_schemes
        self.default_scheme = default_scheme
        self.ignore_http_errors = ignore_http_errors

    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> str:
        value = ("://" not in value) * f"{self.default_scheme}://" + value

        scheme, _ = value.split("://", maxsplit=1)
        if self.permitted_schemes and scheme.lower() not in self.permitted_schemes:
            self.fail(f"The URL {scheme!r} is not supported for this parameter")

        try:
            with urllib.request.urlopen(value) as _:
                pass
        except urllib.error.HTTPError as e:
            if not self.ignore_http_errors:
                self.fail(
                    f"The URL {value!r} returned an HTTP Error ([Error {e.code}] {e.reason})",
                    param, ctx
                )
        except urllib.error.URLError as e:
            self.fail(f"{value!r} is not a valid URL or cannot be opened ({e.reason})", param, ctx)

        return value


def report_http_error(url: str, status_code: int):
    click.secho("ERROR: ", bold=True, fg="red", nl=False, err=True)
    click.echo("The URL ", nl=False, err=True)
    click.secho(url, fg="blue", nl=False, err=True)
    click.echo(" returned an HTTP Error (", nl=False, err=True)
    click.secho(f"{status_code} {HTTP_STATUS_CODES[status_code]}", fg="yellow", nl=False, err=True)
    click.echo(")")


def report_url_error(url: str, message: str):
    click.secho("ERROR: ", bold=True, fg="red", nl=False, err=True)
    click.echo("The URL ", nl=False, err=True)
    click.secho(url, fg="blue", nl=False, err=True)
    click.echo(" is not a valid URL or could not be opened (", nl=False, err=True)
    click.secho(message, fg="yellow", nl=False, err=True)
    click.echo(")")


def report_exception(message: str, exc: BaseException):
    click.secho("ERROR: ", bold=True, fg="red", nl=False, err=True)
    click.echo(message, nl=False, err=True)
    click.echo(" (", nl=False, err=True)
    click.secho(str(exc), fg="yellow", nl=False, err=True)
    click.echo(")")
