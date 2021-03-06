revision = 'fa1b4442dc'
down_revision = 'd5e2ddccb1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('stopword',
        sa.Column('id', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.execute(
        "INSERT INTO stopword(id) VALUES " +
        ", ".join("('%s')" % word for word in word_list)
    )


def downgrade():
    op.drop_table('stopword')


word_list = [
    "a",
    "abia",
    "acea",
    "aceasta",
    "această",
    "aceea",
    "aceia",
    "acel",
    "acela",
    "acelaşi",
    "acele",
    "acelea",
    "aceluiaşi",
    "acest",
    "acesta",
    "aceste",
    "acestea",
    "acestei",
    "aceşti",
    "aceştia",
    "acestor",
    "acestora",
    "acestui",
    "acolo",
    "acum",
    "adică",
    "ai",
    "aia",
    "aici",
    "al",
    "ăla",
    "alături",
    "ale",
    "alt",
    "alta",
    "altă",
    "altceva",
    "alte",
    "altele",
    "altfel",
    "alţi",
    "alţii",
    "altul",
    "am",
    "anume",
    "apoi",
    "ar",
    "are",
    "aş",
    "aşa",
    "asemenea",
    "asta",
    "astăzi",
    "astfel",
    "asupra",
    "atare",
    "atât",
    "atâta",
    "atâtea",
    "atâţi",
    "atâţia",
    "aţi",
    "atît",
    "atîti",
    "atîţia",
    "atunci",
    "au",
    "avea",
    "avem",
    "avut",
    "azi",
    "ba",
    "bine",
    "ca",
    "că",
    "cam",
    "când",
    "care",
    "căreia",
    "cărora",
    "căruia",
    "cât",
    "câtă",
    "câte",
    "câţi",
    "către",
    "ce",
    "cea",
    "ceea",
    "cei",
    "ceilalţi",
    "cel",
    "cele",
    "celelalte",
    "celor",
    "ceva",
    "chiar",
    "ci",
    "cînd",
    "cine",
    "cineva",
    "cît",
    "cîte",
    "cîteva",
    "cîţi",
    "cîţiva",
    "cu",
    "cui",
    "cum",
    "cumva",
    "da",
    "daca",
    "dacă",
    "dar",
    "de",
    "deasupra",
    "decât",
    "deci",
    "decît",
    "deja",
    "deşi",
    "despre",
    "din",
    "dintr",
    "dintre",
    "doar",
    "după",
    "ea",
    "ei",
    "el",
    "ele",
    "era",
    "este",
    "eu",
    "fără",
    "fecăreia",
    "fel",
    "fi",
    "fie",
    "fiecare",
    "fiecărui",
    "fiecăruia",
    "fiind",
    "foarte",
    "fost",
    "i-au",
    "iar",
    "ieri",
    "îi",
    "îl",
    "îmi",
    "împotriva",
    "în",
    "înainte",
    "înapoi",
    "înca",
    "încît",
    "însă",
    "însuşi",
    "într",
    "între",
    "îşi",
    "îţi",
    "l-am",
    "la",
    "le",
    "li",
    "lor",
    "lui",
    "mă",
    "mai",
    "mare",
    "mereu",
    "mod",
    "mult",
    "multă",
    "multe",
    "mulţi",
    "ne",
    "nici",
    "niciodata",
    "nimeni",
    "nimic",
    "nişte",
    "noi",
    "noştri",
    "nostru",
    "nouă",
    "nu",
    "numai",
    "o",
    "oarecare",
    "oarece",
    "oarecine",
    "oarecui",
    "or",
    "orice",
    "oricum",
    "până",
    "pe",
    "pentru",
    "peste",
    "pînă",
    "plus",
    "poată",
    "prea",
    "prin",
    "printr-o",
    "puţini",
    "s-ar",
    "sa",
    "să",
    "să-i",
    "să-mi",
    "să-şi",
    "să-ţi",
    "săi",
    "sale",
    "sau",
    "său",
    "se",
    "şi",
    "sînt",
    "sîntem",
    "sînteţi",
    "spre",
    "sub",
    "sunt",
    "suntem",
    "sunteţi",
    "te",
    "ţi",
    "toată",
    "toate",
    "tocmai",
    "tot",
    "toţi",
    "totul",
    "totuşi",
    "tu",
    "tuturor",
    "un",
    "una",
    "unde",
    "unei",
    "unele",
    "uneori",
    "unii",
    "unor",
    "unui",
    "unul",
    "va",
    "vă",
    "voi",
    "vom",
    "vor",
    "vreo",
    "vreun",
]
