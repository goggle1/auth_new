#coding:utf8
import os
import time
import logging
import httplib
import urllib


import db
import config

class DbIoMessage:
    def __init__(self, timestamp, mac_addr, sn, x_forwarded_for, x_real_ip):
        self.timestamp = timestamp
        self.mac_addr  = mac_addr
        self.sn        = sn
        self.x_forwarded_for    = x_forwarded_for
        self.x_real_ip          = x_real_ip


def notify_java_auth_new(target_ip, target_port, mac_addr, sn, x_forwarded_for, x_real_ip):    
    logging.info('notify_java_auth_new ip=[%s], port=[%d], mac_addr=[%s], sn=[%s], X-Forwarded-For=[%s], X-Real-IP=[%s]' % (target_ip, target_port, mac_addr, sn, x_forwarded_for, x_real_ip))  
    ret = False        
    try:        
        ip = target_ip
        port = target_port
        the_url = "/auth_new" 
        #mac_addr_line = "%s\r\n" % (mac_addr)
        mac_addr_line = "%s" % (mac_addr)
        mac_addr_quote = urllib.quote(mac_addr_line)
        #sn_line = "%s\r\n" % (sn)
        sn_line = "%s" % (sn)
        sn_quote = urllib.quote(sn_line)
        the_body = "macAddr=%s&sn=%s" % (mac_addr_quote, sn_quote)   
        the_headers = {}
        the_headers["Content-Type"]     = "application/x-www-form-urlencoded" 
        the_headers["X-Forwarded-For"]  =  x_forwarded_for 
        the_headers["X-Real-IP"]        = x_real_ip  
        conn = httplib.HTTPConnection(ip, port, True, 10)  
        conn.request(method="POST", url=the_url, body=the_body, headers=the_headers)
        response = conn.getresponse()
        if response.status == 200:      
            logging.info('notify_java_auth_new success, url=[%s], body=[%s]' % (the_url, the_body))
            ret = True
        else:      
            logging.info('notify_java_auth_new failure, url=[%s], body=[%s]' % (the_url, the_body))
            ret = False
        response_content = response.read()
        logging.info('notify_java_auth_new recv content=[%s]' % (response_content))
        conn.close()
    except Exception, e:             
        logging.error('notify_java_auth_new error=[%s], url=[%s], body=[%s]' % (e, the_url, the_body))
        ret = False            
    return ret        

        
class DbMaster:
    def __init__(self, ip, port):
        self.java_ip    = ip
        self.java_port  = port
        self.the_db     = db.DB_MYSQL()
        try: 
            self.the_db.connect(config.DB_CONFIG.host, config.DB_CONFIG.port, config.DB_CONFIG.user, config.DB_CONFIG.password, config.DB_CONFIG.db)
        except Exception, e:
            logging.error('DbMaster.__init__(), error=[%s]' %(e))        
        
        
    def ReconnectDb(self):
        try:
            self.the_db.close()
            self.the_db.connect(config.DB_CONFIG.host, config.DB_CONFIG.port, config.DB_CONFIG.user, config.DB_CONFIG.password, config.DB_CONFIG.db)
        except Exception, e:
            logging.error('DbMaster.ReconnectDb(), error=[%s]' %(e))
            return False
        return True

    
    def DoMessage(self, one_message):
        mac_exist = False
        logging.info("process DoMessage one_message=[%s,%s,%s,%s,%s]" %(one_message.timestamp, one_message.mac_addr, one_message.sn, one_message.x_forwarded_for, one_message.x_real_ip))
        #one_sql =   "select 1 from DEV_DEVICE where DEVICE_KEY = '%s'" % (one_message.api_key)
        #try:    
        #    result = self.the_db.execute(one_sql)        
        #    logging.info("result=[%d], sql=[%s]" % (result, one_sql))
        #    if(result > 0):
        #        mac_exist = True
        #except Exception, e:
        #    logging.error('DbMaster.DoMessage() error=[%s], sql=[%s]' %(e, one_sql))
            #return False        
        if(mac_exist == False):
            notify_java_auth_new(self.java_ip, self.java_port, one_message.mac_addr, one_message.sn, one_message.x_forwarded_for, one_message.x_real_ip)
        return True
         
        
        
def ProcessMessage(process_index, one_queue):
    log_file_name = config.LOG_TEMPLATE % (process_index)
    #logging.basicConfig(filename=log_file_name, level=logging.INFO)
    rotate_handler = logging.handlers.TimedRotatingFileHandler(log_file_name, 'H', 1, 0)
    rotate_handler.suffix = "%Y%m%d%H"
    str_format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line.%(lineno)d: %(message)s'    
    log_format = logging.Formatter(str_format)
    rotate_handler.setFormatter(log_format)
    logging.getLogger('').addHandler(rotate_handler)
    logging.getLogger().setLevel(logging.INFO)  
    
    pid = os.getpid()
    logging.info("process index=%d pid=%d start..." % (process_index, pid))
    
    java_server = config.JAVA_SERVER_LIST[process_index]
    db_master = DbMaster(java_server.host, java_server.port)
        
    while(1):
        logging.info("process queue size=%d" % (one_queue.qsize()))
        one_message = one_queue.get()        
        logging.info("process deque one_message=[%s,%s,%s]" %(one_message.timestamp, one_message.mac_addr, one_message.sn))        
        ret = db_master.DoMessage(one_message) 
        if(ret == False):
            db_master.ReconnectDb()
            ret = db_master.DoMessage(one_message)
            