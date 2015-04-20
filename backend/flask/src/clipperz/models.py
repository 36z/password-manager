import datetime

from flask.ext.login import UserMixin

from clipperz import app, db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, index=True)
    srp_s = db.Column(db.String(128))
    srp_v = db.Column(db.String(128))
    header = db.Column(db.Text())
    statistics = db.Column(db.Text())
    auth_version = db.Column(db.String())
    version = db.Column(db.String())
    lock = db.Column(db.String())
    records = db.relationship(
        'Record',
        backref='user',
        lazy='dynamic',
        cascade='save-update, merge, delete, delete-orphan')
    otps = db.relationship(
        'OneTimePassword',
        backref='user',
        lazy='dynamic',
        cascade='save-update, merge, delete, delete-orphan')
    offline_saved = db.Column(db.Boolean(), default=False)
    update_date = db.Column(db.DateTime(), nullable=True)

    def updateCredentials(self, credentials):
        self.username = credentials['C']
        self.srp_s = credentials['s']
        self.srp_v = credentials['v']
        self.auth_version = credentials['version']

    def update(self, data):
        self.header = data['header']
        self.statistics = data['statistics']
        self.version = data['version']
        if 'lock' in data:
            self.lock = data['lock']
        self.update_date = datetime.datetime.utcnow()
        self.offline_saved = False

    def __repr__(self):
        return '<User %r>' % (self.username)

#------------------------------------------------------------------------------


class RecordVersion(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    reference = db.Column(db.String(), unique=True, index=True)
    header = db.Column(db.Text())
    data = db.Column(db.Text())
    api_version = db.Column(db.String())
    version = db.Column(db.Integer())
    previous_version_key = db.Column(db.String())
    previous_version_id = db.Column(db.Integer(),
                                    db.ForeignKey('record_version.id'))
    creation_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    update_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    access_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    record_id = db.Column(db.Integer(),
                          db.ForeignKey('record.id'),
                          nullable=False)

    record = db.relationship('Record',
                             backref=db.backref('record_versions',
                                                order_by=id,
                                                cascade='all,delete'))

    def update(self, someData):
        app.logger.debug(someData)
        recordVersionData = someData['currentRecordVersion']
        self.reference = recordVersionData['reference']
        self.data = recordVersionData['data']
        self.api_version = recordVersionData['version']
        self.version = self.record.version
        self.previous_version_key = recordVersionData['previousVersionKey']
        self.update_date = datetime.datetime.utcnow()

        self.record.update(someData['record'], self)
#------------------------------------------------------------------------------


class Record(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.ForeignKey('user.id'))
    reference = db.Column(db.String(), unique=True, index=True)
    data = db.Column(db.Text())
    api_version = db.Column(db.String())
    version = db.Column(db.Integer(), default=0)
    creation_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    update_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    access_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    current_record_version = db.relationship(
        'RecordVersion',
        uselist=False,
        cascade='save-update, merge, delete, delete-orphan')

    def update(self, data, record_version):
        self.reference = data['reference']
        self.data = data['data']
        self.api_version = data['version']
        self.update_date = datetime.datetime.now()
        self.current_record_version = record_version
        if self.version:
            self.version += 1
        else:
            self.version = 1

#------------------------------------------------------------------------------


class OneTimePassword(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.ForeignKey('user.id'))
    status = db.Column(db.String())
    reference = db.Column(db.String(), unique=True)
    key_value = db.Column(db.String())
    key_checksum = db.Column(db.String())
    data = db.Column(db.Text())
    version = db.Column(db.String())
    creation_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    request_date = db.Column(db.DateTime())
    usage_date = db.Column(db.DateTime())

    def update(self, someParameters, aStatus):
        self.reference = someParameters['reference']
        self.key_value = someParameters['key']
        self.key_checksum = someParameters['keyChecksum']
        self.data = someParameters['data']
        self.version = someParameters['version']
        self.status = aStatus

    def reset(self, aStatus):
        self.data = ""
        self.status = aStatus
        return self

#------------------------------------------------------------------------------


class Session(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    sessionId = db.Column(db.String())
    access_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
