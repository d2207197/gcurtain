
import pp
from apistar import App, Route, http

from .cli import cli_app


def welcome(name=None):
    if name is None:
        return {'message': 'Welcome to API Star!'}
    return {'message': 'Welcome to API Star, %s!' % name}


def calendar_notification(request: http.Request) -> dict:
    print({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    })

    pp(dict(request.headers))
    return http.Response()


routes = [
    Route('/calendar/notification', method='POST',
          handler=calendar_notification),
]

app = App(routes=routes)


if __name__ == '__main__':
    cli_app.run()
    # app.serve('127.0.0.1', 8000, use_debugger=True, use_reloader=True)
