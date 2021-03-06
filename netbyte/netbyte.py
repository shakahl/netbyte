#                __  __          __
#    ____  ___  / /_/ /_  __  __/ /____
#   / __ \/ _ \/ __/ __ \/ / / / __/ _ \
#  / / / /  __/ /_/ /_/ / /_/ / /_/  __/
# /_/ /_/\___/\__/_.___/\__, /\__/\___/
#                      /____/
#                       Author: sc0tfree
#                       Twitter: @sc0tfree
#                       Email: henry@sc0tfree.com

import socket
import errno
import argparse
import sys
import time
from colorama import Fore, Style
from threading import Thread
from Queue import Queue, Empty


def is_symbol(character):
    '''
    Checks to see if a character is a symbol.

    Returns:
        bool: True if character is symbol
    '''
    symbols = "~`!@#$%^&*()_-+={}[]:>;',</?*-+"
    if character not in symbols:
        return False
    else:
        return True


def to_hex(string):
    '''
    Converts string to formatted hex and ASCII reference values

    Returns:
        str: Formatted hex & ASCII reference
    '''

    results = []

    new_line = True

    for character in string:

        # Convert ASCII to unicode
        unicode_value = ord(character)

        # Convert unicode to hex
        hex_value = hex(unicode_value).replace('0x', '')

        # Add a preceding 0
        if len(hex_value) == 1:
            hex_value = '0' + hex_value

        # Make upper case
        hex_value = hex_value.upper()

        # Add reference ASCII for readability
        if character.isalpha() or character.isdigit() or is_symbol(character):
            hex_value = hex_value + '(' + character + ')'

        # Add a space in between hex values (not to a new line)
        if not new_line:
            hex_value = ' ' + hex_value

        # Add a newline for readability (corresponding to ASCII)
        if '0A' in hex_value and not string.isspace():
            hex_value = hex_value + '(\\n)\n'
            # Next line will be a newline
            new_line = True
        else:
            new_line = False

        results.append(hex_value)

    full_hex = ''
    for result in results:
        full_hex += result

    return full_hex


def print_ascii(string):
    '''
    Print string with ASCII color configuration
    '''
    if string.isspace():
        # Add a space to show colors on a non-ASCII line
        string = ' ' + string
    print(Fore.MAGENTA + Style.BRIGHT + string + Style.RESET_ALL)


def print_hex(string):
    '''
    Print string with hex color configuration
    '''
    print(Fore.BLUE + Style.BRIGHT + string + Style.RESET_ALL)


def print_error(string):
    '''
    Print string with error color configuration and exit with code 1
    '''
    print(Fore.RED + Style.BRIGHT + string + Style.RESET_ALL)
    exit(1)


class ReadAsync(object):
    '''
    ReadAsync starts a queue thread to accept stdin
    '''
    def __init__(self, blocking_function, *args):
        self.args = args

        self.read = blocking_function

        self.thread = Thread(target=self.enqueue)

        self.queue = Queue()

        self.thread.daemon = True

        self.thread.start()

    def enqueue(self):
        while True:
            buffer = self.read(*self.args)
            self.queue.put(buffer)

    def dequeue(self):
        return self.queue.get_nowait()


def description():
    '''
    argparse description text
    '''
    return '''
Netbyte is a Netcat-style tool that facilitates probing proprietary TCP and UDP services.
It is lightweight, fully interactive and provides formatted output in both hexadecimal and ASCII.'''


def parse_arguments():
    '''
    Parse command line arguments

    Returns:
        argparse Namespace object
    '''
    parser = argparse.ArgumentParser(description=description(), formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('hostname', metavar='HOSTNAME', help='Host or IP to connect to')
    parser.add_argument('port', metavar='PORT', help='Connection port')
    parser.add_argument('-u', dest='udp', action="store_true", default=False, help='Use UDP instead of default TCP')

    if len(sys.argv) == 1:

        parser.print_help()

        exit(1)

    args = parser.parse_args()
    return args


def main():
    '''
    Main function: Connects to host/port and spawns ReadAsync
    '''

    args = parse_arguments()

    if args.udp:
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    connection.settimeout(2)

    address = (args.hostname, int(args.port))

    try:
        connection.connect(address)

    except socket.error:
        print_error("Could not establish connection to " + address[0] + ":" + str(address[1]))

    print(Fore.GREEN + Style.BRIGHT + "Connection established" + Style.RESET_ALL)

    try:
        connection.setblocking(0)
        stdin = ReadAsync(sys.stdin.readline)

        while True:
            try:
                data = connection.recv(4096)
                if not data:
                    raise socket.error
                print_ascii(data)
                print_hex(to_hex(data))
            except socket.error, e:
                if e.errno != errno.EWOULDBLOCK:
                    raise
            try:
                connection.send(stdin.dequeue())
            except Empty:
                time.sleep(0.1)

    except KeyboardInterrupt:
        connection.close()
        print_error("\nExiting...")
    except socket.error:
        print_error("Connection closed")