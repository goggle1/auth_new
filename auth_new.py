# coding: utf-8
import os
import json
import logging
import tornado
import tornado.ioloop
import tornado.web
import tornado.httpserver

import multiprocessing

import time
import base64
import hashlib

import config
import db_io

g_message_queue_list = []

def md5sum(src_str):    
    m = hashlib.md5()   
    m.update(src_str)
    return m.hexdigest()

        
def SendMessageToDbIo(timestamp, mac_addr, sn, x_forwarded_for, x_real_ip):
    one_message = db_io.DbIoMessage(timestamp, mac_addr, sn, x_forwarded_for, x_real_ip)    
    global g_message_queue_list
    queue_size = len(g_message_queue_list)
    pid = os.getpid()
    queue_index = pid%queue_size
    logging.info("queue_size=%d, pid=%d, queue_index=%d" % (queue_size, pid, queue_index))
    one_queue = g_message_queue_list[queue_index]
    one_queue.put(one_message)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, I am auth_new master.<p>\n")

        
class AuthNewHandler(tornado.web.RequestHandler):
    def post(self):
        x_forwarded_for = ""
        print self.request.headers
        logging.info("%s" % (self.request.headers))
        if(self.request.headers.has_key("X-Forwarded-For")):
            x_forwarded_for = self.request.headers["X-Forwarded-For"] 
        x_real_ip = ""
        if(self.request.headers.has_key("X-Real-IP")):            
            x_real_ip = self.request.headers["X-Real-IP"] 
        if(self.request.headers.has_key("X-Real-Ip")):            
            x_real_ip = self.request.headers["X-Real-Ip"]
        mac_addr = self.get_argument("macAddr", "null") 
        sn       = self.get_argument("sn", "null")
        now_second  = time.time()
        now_time    = time.localtime(now_second)    
        timestamp   = time.strftime("%Y%m%d%H%M%S", now_time)       
        logging.info("time=[%s], X-Forwarded-For=[%s], X-Real-IP=[%s], mac=[%s], sn=[%s]" % (timestamp, x_forwarded_for, x_real_ip, mac_addr, sn))
        SendMessageToDbIo(timestamp, mac_addr, sn, x_forwarded_for, x_real_ip)        
        the_response = '{"code":"A000000","message":"OK","timestamp":"%s"}' % (timestamp)        
        self.write(the_response)
        

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    #"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    #"login_url": "/login",
    #"xsrf_cookies": True,
}

application = tornado.web.Application([
    (r"/",                          MainHandler),
    (r"/auth_new",                  AuthNewHandler),
    (r"/static/(.*)",               tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
    #(r"/.*\.html",                  tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
    
], **settings)

if __name__ == "__main__":    
    for process_index in range(0, config.DB_IO_NUM, 1):
        message_queue = multiprocessing.Queue()
        g_message_queue_list.append(message_queue)
        process = multiprocessing.Process(target=db_io.ProcessMessage, args=(process_index, message_queue))
        process.start()    
    
    #logging.basicConfig(filename=config.LOG_FILENAME, level=logging.INFO)
    rotate_handler = logging.handlers.TimedRotatingFileHandler(config.LOG_FILENAME, 'H', 1, 0)
    rotate_handler.suffix = "%Y%m%d%H"
    str_format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line.%(lineno)d: %(message)s'    
    log_format = logging.Formatter(str_format)  
    rotate_handler.setFormatter(log_format)
    logging.getLogger('').addHandler(rotate_handler)
    logging.getLogger().setLevel(logging.INFO)        
    
    logging.info('listen @%d ......' % (config.LISTEN_PORT))
    #application.listen(config.LISTEN_PORT)
    #tornado.ioloop.IOLoop.instance().start()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(config.LISTEN_PORT)
    http_server.start(config.PROCESS_NUM)
    tornado.ioloop.IOLoop.instance().start()
    