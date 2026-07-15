from garlicsmtp.smtp.engine import SMTPEngine

from garlicsmtp.smtp.session import SMTPSession

engine = SMTPEngine()

session = SMTPSession("127.0.0.1")

session.state = session.state.RECEIVE_DATA

lines = [

    "Subject: Test",

    "",

    "Prima riga",

    "Seconda riga",

    "."

]

for line in lines:

    done = engine.receive_data(

        session,

        line

    )

    if done:

        break

