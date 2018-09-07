# -*- coding: utf-8 -*-
"""Main module."""

import threading
import pymysql

def create_pool(pymysql_args, max_count=10, timeout=10):
    return ConnectionPool(pymysql_args, max_count, timeout)

class ConnectionPool(object):
    def __init__(self, pymysql_args, max_count=10, timeout=60):
        self.pymysql_args = pymysql_args
        self.max_count = max_count
        self.timeout = timeout
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.in_use_list = set()
        self.free_list = set()

    def new_connection(self):
        connection =  pymysql.connect(**self.pymysql_args)
        connection.connection_pool = self
        return connection

    def get_from_free_list(self):
        connection = self.free_list.pop()
        if connection.open is False:
            connection = self.new_connection()
        return connection

    def get(self):
        with self.lock:
            if len(self.free_list) > 0:
                connection = self.get_from_free_list()
            elif len(self.in_use_list) < self.max_count:
                connection = self.new_connection()
            elif len(self.free_list) == 0:
                self.condition.wait(self.timeout)
                if len(self.free_list) == 0:
                    raise TimeoutError()
                else:
                    connection = self.get_from_free_list()
            self.in_use_list.add(connection)
            return connection


    def return_to_pool(self, value):
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
    if self.connection_pool != None:
        self.connection_pool.return_to_pool(self)
    elif self.original_close != None:
        self.original_close()


def modified_close(self):
    if self.connection_pool != None:
        self.connection_pool.return_to_pool(self)
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
