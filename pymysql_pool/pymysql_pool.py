# -*- coding: utf-8 -*-
"""Main module."""

import threading
import pymysql

def create_pool(pymysql_args, max_count=10, timeout=10):
    return ConnectionPool(pymysql_args, max_count, timeout)

class ConnectionPool(object):
    def __init__(self, pymysql_args, max_count=10, timeout=10):
        self.pymysql_args = pymysql_args
        self.max_count = max_count
        self.timeout = timeout
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.in_use_list = set()
        self.free_list = set()

    def new_connection(self):
        return pymysql.connect(**self.pymysql_args)

    def get(self):
        with self.lock:
            if len(self.free_list) > 0:
                conn = self.free_list.pop()
                if conn.open is False:
                    conn = self.new_connection()
                self.in_use_list.add(conn)
                return conn
            if len(self.in_use_list) < self.max_count:
                conn = self.new_connection()
                conn.pooling = self
                self.free_list.add(conn)
            if len(self.free_list) <= 0:
                self.condition.wait(self.timeout)
                if len(self.free_list) <= 0:
                    raise TimeoutError()
            conn = self.free_list.pop()
            self.in_use_list.add(conn)
            return conn

    def put(self, value):
        with self.lock:
            self.in_use_list.remove(value)
            self.free_list.add(value)
            self.condition.notify_all()

    def size(self):
        with self.lock:
            return len(self.free_list) + len(self.in_use_list)

    def max_size(self):
        return self.max_count

def modified_enter(self):
    return self

def modified_exit(self, type, value, traceback):
    if self.pooling != None:
        self.pooling.put(self)
    elif self.original_close != None:
        self.original_close()


def modified_close(self):
    if self.pooling != None:
        self.pooling.put(self)
    elif self.old_close != None:
        self.old_close()

def __modify_pymysql_connection_close():
    original_close = pymysql.connections.Connection.close
    if original_close == modified_close:
        return
    pymysql.connections.Connection.close = modified_close
    pymysql.connections.Connection.original_close = original_close

def __modify_pymysql_connection_enter():
    original_enter = pymysql.connections.Connection.__enter__
    if original_enter == modified_enter:
        return
    pymysql.connections.Connection.__enter__ = modified_enter
    pymysql.connections.Connection.original_enter = original_enter

def __modify_pymysql_connection_exit():
    original_exit = pymysql.connections.Connection.__exit__
    if original_exit == modified_exit:
        return
    pymysql.connections.Connection.__exit__ = modified_exit
    pymysql.connections.Connection.original_exit = original_exit

__modify_pymysql_connection_close()
__modify_pymysql_connection_enter()
__modify_pymysql_connection_exit()
