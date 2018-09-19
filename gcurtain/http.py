
from urllib.parse import quote as urlquote

import pp
from apistar import App, Route, http, types, validators

from gcurtain import trello


def calendar_notification(request: http.Request) -> dict:
    print({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    })

    pp(dict(request.headers))
    return http.Response()


class AppointmentRequest(types.Type):
    name = validators.String(max_length=100)
    phone = validators.String(max_length=100)
    addr = validators.String(max_length=200)
    progress = validators.String(max_length=100)
    comment = validators.String(max_length=200)

    def format_title(self):
        return f'{self.name} {self.phone} {self.addr}'

    def format_details(self):
        return (f'姓名: {self.name}\n'
                f'電話: {self.phone}\n'
                f'地址: {self.addr}\n'
                f'裝潢進度: {self.progress}\n'
                f'備註：{self.comment}'
                )

    def format_add_to_calendar_link(self):
        text = '量 ' + self.format_title()
        return (
            f'https://www.google.com/calendar/render?action=TEMPLATE'
            f'&text={urlquote(text)}'
            f'&location={urlquote(self.addr)}'
            f'&details={urlquote(self.format_details())}'
        )


def trello_add_appointment_req(appointment_req: AppointmentRequest):
    print('Appointment Request Received:')
    print(appointment_req)

    card_desc = (('新增到 Google Calendar: '
                  f'{appointment_req.format_add_to_calendar_link()}\n\n')
                 + appointment_req.format_details())

    appointment_req_tlist = trello.agent.tlist_of_name_opt('預約').value
    card = appointment_req_tlist.add_card(
        name=appointment_req.format_title(),
        position='bottom',
        desc=card_desc,
    )
    print('Card added:')
    pp(card)
    return {}


routes = [
    Route('/calendar/notification', method='POST',
          handler=calendar_notification),
    Route('/trello/appointment_req', method='POST',
          handler=trello_add_appointment_req),
]
app = App(routes=routes)
