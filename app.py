import flask
import pymysql
import datetime
import config
import os

app = flask.Flask("shortlinkSystem", static_url_path="/public", static_folder="web/public", template_folder="web/templates")

def prepare_database():
    db = pymysql.connect(
        host=config.mysql["host"],
        user=config.mysql["user"],
        password=config.mysql["password"],
        database=config.mysql["db"]
    )
    
    table_sql = "CREATE TABLE IF NOT EXISTS `shortlinks` (`id` bigint(20) NOT NULL, `short` varchar(10) NOT NULL, `longlink` varchar(500) NOT NULL, `delay` int(11), `created` datetime NOT NULL, PRIMARY KEY (id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"

    cursor = db.cursor()
    # Creates the table for shortlinks
    cursor.execute(table_sql)
    # Turn on auto increment
    cursor.execute("ALTER TABLE `shortlinks` MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;")

def get_shortlink(shortlink):
    db = pymysql.connect(
        host=config.mysql["host"],
        user=config.mysql["user"],
        password=config.mysql["password"],
        database=config.mysql["db"]
    )
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM shortlinks WHERE short = %s", (shortlink))

    rows = cursor.fetchall()

    link = {}
    for row in rows:
        link["id"] = row[0]
        link["short"] = row[1]
        link["redirect"] = row[2]
        link["delay"] = row[3]
        link["created"] = row[4]

    if link != {}:
        return link
    else:
        return "error"

def create_shortlink(longlink, delay):
    if not longlink.__contains__("https://") and not longlink.__contains__("http://") or not longlink.__contains__("."):
        return "invalid longlink"
    
    if not delay.isdigit():
        return "invalid delay"

    db = pymysql.connect(
        host=config.mysql["host"],
        user=config.mysql["user"],
        password=config.mysql["password"],
        database=config.mysql["db"]
    )

    cursor = db.cursor()
    shortlink = os.urandom(2).hex()
    
    valid = False
    while valid != True:
        cursor.execute("SELECT * FROM shortlinks WHERE short = %s", (shortlink))
        rows = cursor.fetchall()
        if len(rows) > 0:
            valid = False
            shortlink = os.urandom(2).hex()
        else:
            valid = True

    dt = str(datetime.datetime.now()).split(".")[0]
    cursor.execute("INSERT INTO shortlinks VALUES (0, %s, %s, %s, %s)", (shortlink, longlink, delay, dt))
    db.commit()

    return shortlink

######### WEB PAGES ###########

@app.route("/")
def index():
    return flask.redirect(config.mainPage)

@app.route("/admin")
def admin():
    params = flask.request.args
    if params["token"] == config.adminToken:
        return flask.render_template("index.html")
    else:
        return "Wrong token."

@app.route("/<shortlink>")
def short(shortlink):
    link = get_shortlink(shortlink=shortlink)
    return flask.render_template("shortlink.html", link=link)

############ API #############

@app.route("/api/get/<shortlink>")
def get(shortlink):
    link = get_shortlink(shortlink=shortlink)
    return link

@app.route("/api/create", methods=["POST"])
def create():
    params = flask.request.get_json()
    return create_shortlink(longlink=params["longlink"], delay=params["delay"])

if __name__ == "__main__":
    prepare_database()
    app.run("127.0.0.1", config.port)
