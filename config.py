# coding: utf-8

LISTEN_PORT  = 9002
PROCESS_NUM  = 24
DB_IO_NUM    = 3
LOG_FILENAME = "/data/auth_new/logs/access.log"
LOG_TEMPLATE = "/data/auth_new/logs/process_%d.log"


class JAVA_SERVER_1:
    host        = '10.1.15.102'
    port        = 8003

class JAVA_SERVER_2:
    host        = '10.1.15.102'
    port        = 8003
    
class JAVA_SERVER_3:
    host        = '10.1.15.102'
    port        = 8003
    
JAVA_SERVER_LIST = [JAVA_SERVER_1, JAVA_SERVER_2, JAVA_SERVER_3]

class DB_CONFIG:
    host        = '10.53.130.23'
    port        = 3306
    user        = 'gitv_rd'
    password    = '1234.gitv_rd'
    db          = 'ibcp'
    table       = 'xxx'
    
    