from mptracker.models import db, Text, TextVersion


def get_text(ns, name):
    text = Text.query.filter_by(ns=ns, name=name).first()
    if text:
        version = text.versions.order_by(TextVersion.time.desc()).first()
        if version:
            return {
                'content': version.content,
                'more_content': version.more_content,
            }

    return {'content': "", 'more_content': ""}


def save_text(ns, name, content, more_content):
    text = Text.query.filter_by(ns=ns, name=name).first()
    if not text:
        text = Text(ns=ns, name=name)
        db.session.add(text)

    TextVersion(text=text, content=content, more_content=more_content)
    db.session.commit()


def get_text_list():
    rv = set()

    for text in Text.query:
        rv.add((text.ns, text.name))

    return sorted(rv)
