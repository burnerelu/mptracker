from datetime import date, datetime
from contextlib import contextmanager
import subprocess
import tempfile
import csv
import re
from io import StringIO
from itertools import chain
import flask
from werkzeug.routing import BaseConverter, ValidationError
from werkzeug.urls import url_decode, url_parse
from flask.ext.rq import job
from babel.dates import format_date
from psycopg2.extras import DateRange
from path import path

MAX_OCR_PAGES = 3

common = flask.Blueprint('common', __name__)


class UuidConverter(BaseConverter):

    def to_python(self, value):
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                    r'[0-9a-f]{4}-[0-9a-f]{12}$', value) is None:
            raise ValidationError
        return value


@common.record
def register_url_converters(state):
    app = state.app
    app.url_map.converters['uuid'] = UuidConverter


@common.app_template_filter('datefmt')
def datefmt(value):
    if value in [date.min, date.max]:
        return ""
    return format_date(value, 'd MMMM y', locale='ro')


def parse_date(date_str):
    return date_str and datetime.strptime(date_str, '%Y-%m-%d').date()


def parse_date_range(date_range_str):
    if not date_range_str:
        return None
    m = re.match(r'^\[(?P<lower>\S+), (?P<upper>\S+)\)$', date_range_str)
    return DateRange(
        parse_date(m.group('lower')),
        parse_date(m.group('upper')),
    )


def fix_local_chars(txt):
    return (txt.replace("ş", "ș").replace("Ş", "Ș")
               .replace("ţ", "ț").replace("Ţ", "Ț"))


@contextmanager
def temp_dir():
    tmp = path(tempfile.mkdtemp())
    try:
        yield tmp
    finally:
        tmp.rmtree()


@job
def ocr_url(url, max_pages=MAX_OCR_PAGES):
    from mptracker.scraper.common import create_session

    pdf_cache_name = flask.current_app.config.get('MPTRACKER_PDF_CACHE')
    http_session = create_session(cache_name=pdf_cache_name, throttle=0.5)

    with temp_dir() as tmp:
        pdf_data = http_session.get(url).content
        pdf_path = tmp / 'document.pdf'
        with pdf_path.open('wb') as f:
            f.write(pdf_data)
        subprocess.check_call(['pdfimages', pdf_path, tmp / 'img'])

        pages = []
        for image_path in sorted(tmp.listdir('img-*'))[:MAX_OCR_PAGES]:
            subprocess.check_call(['tesseract',
                                   image_path, image_path,
                                   '-l', 'ron'],
                                  stderr=subprocess.DEVNULL)
            text = (image_path + '.txt').text()
            pages.append(text)

        return pages


def csv_lines(cols, rows):
    out = StringIO()
    writer = csv.DictWriter(out, cols)
    header = dict(zip(cols, cols))
    for r in chain([header], rows):
        writer.writerow(r)
        yield out.getvalue()
        out.seek(out.truncate(0))


def model_to_dict(model, namelist):
    rv = {}
    for name in namelist:
        rv[name] = getattr(model, name)
    return rv


def url_args(url):
    return url_decode(url_parse(url).query)
