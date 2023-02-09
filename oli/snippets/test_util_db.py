import psycopg2
from utils.dictfile import readDictFile

def try_this():
    conn = ConnToOliDB()
    print(conn.init_result)
    
class ConnToOliDB(object):
    '''Class for connecting to the postgresql database as defined in oli.config
    Methods implemented now are read subjects and add subjects '''
    def __init__(self):
        'let us create the connection to use multiple times'
        config=readDictFile('oli.config')
        conn_string = "host='%s' dbname='%s' user='%s' password='%s' port='%s'" % (config['dbHost'], config['dbName'], config['dbUser'], config['dbPass'], config['dbPort'])
        self.init_result = ''
        
        # get a connection, if a connect cannot be made an exception will be raised here
        try:
            self._conn = psycopg2.connect(conn_string)
            connect_result = 'INFO: class connected to %s, %s as %s on port %s' % (config['dbHost'], config['dbName'], config['dbUser'], config['dbPort'])
        except psycopg2.OperationalError  as e:
            connect_result = format(e)
        
        self.init_result = connect_result



if __name__ == '__main__':
    try_this()