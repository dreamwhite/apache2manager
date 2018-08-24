#!/usr/bin/python3
# -*- coding: utf-8 -*-
#MAIN LIBRARIES
import getpass
import os
import pprint
import re
import readline
import socket
import sys
import subprocess
import time
from shutil import *
from color import *
from pysed import * #External Library 

class Apache2Manager():
        
    def __init__(self):

        if not os.geteuid() == 0: #Checks if the user running this script is root
            sys.exit("\nOnly root can run this script\n")

        self.available_sites_path = "/etc/apache2/sites-available" #Available sites path
        self.domain = ".dreamwhite.io" #Domain
        self.email = "webmaster@localhost" #Email
        self.enabled_sites_path = "/etc/apache2/sites-enabled" #Enabled sites path
        self.etc_initd_path = "/etc/init.d/" #Path for php versions
        self.hosts_file = "/etc/hosts" #Hosts file
        self.template_vhost = "/etc/apache2/sites-available/template" #Template file
        self.user = os.environ["SUDO_USER"] #This script is intended to be run with sudo
        self.www_data_group = "www-data" #www-data group

        self.regex_url = r"(?<=ServerName ).*(?=)" #Regex expression for getting the URL
        self.regex_docroot = r"(?<=DocumentRoot ).*?(?=\n)" #Regex expression for getting the docroot
        self.regex_directory = r"(?<=<Directory ).*?(?=\/>)" #Regex expression for getting the docroot
        self.regex_php = r"""(?<=SetHandler "proxy:unix:\/var\/run\/php\/).*(?=.sock\|fcgi:\/\/localhost\/)""" #Regex expression for getting the PHP Version

        self.sites = []
        self.php_version = []
        self.FNULL = open(os.devnull, 'w') #/dev/null

        global sites
        global php_version

    def commands(self):

        commands = [

            '?',
            'del',
            'dis',
            'edit',
            'ena',
            'help',
            'info',
            'rem',
            "add",
            "close",
            "create",
            "delete",
            "destroy",
            "disable",
            "edit",
            "enable",
            "exit",
            "help",
            "list",
            "new",
            "quit",
            "remove",
            "show",

        ] #Commands

        return commands


class Messages(): #Custom messages class

    def command_not_found(self, command):

        print(FAIL + "Command not found: " + CYAN + command + ENDC)

    def warning(self, message):

        print(WARNING + message + ENDC)

    def correct(self, message):

        print(OKGREEN + message + ENDC)

    def error(self, message):

        print(FAIL + message + ENDC)

    def clear_console(self):

        time.sleep(0.1)

        print("\033c") #Code for clearing the console and block the scroll up

class Add():

    manager = Apache2Manager()
    messages = Messages()

    def docroot(self, docroot):

        if not docroot.startswith('/var/www/'): #If docroot not starts with /var/www adds

            docroot = '/var/www/{0}'.format(docroot)

        subprocess.call('mkdir {0}'.format(docroot), shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

    def hosts_entry(self, url): #Writes on the /etc/hosts file the entry for the VHost

        with open(self.manager.hosts_file, 'a') as hosts:

            hosts.write("\n127.0.0.1       {0}".format(url))

class Delete():

    manager = Apache2Manager()
    messages = Messages()

    def var_www(self, url, delete_www_path): #Delete docroot
    
        subprocess.call("rm -r {0}".format(delete_www_path), shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
        self.messages.correct("Successfully removed the www of {0}!".format(url))

    def from_etc_hosts(self, url): #Delete from hosts file

        rmlinematch('127.0.0.1       {0}'.format(url), self.manager.hosts_file)
        self.messages.correct("Site {0} deleted successfully from /etc/hosts file".format(url))

    def vhost_conf(self, url, vhost): #Delete vhost configuration file

        subprocess.call("rm {0}".format(vhost), shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
        self.messages.correct("VHost configuration file for {0} successfully deleted!".format(url))

class Helper():
    
    def grid(self, array): #Create grid

        copy_array = array[:]
        nums_per_row = 4
        nums_in_row = 1

        for i in range(len(array)):

            if nums_in_row % nums_per_row == 0:

                copy_array[i] = HEADER + \
                    OKGREEN + copy_array[i] + DEFAULT + "\n"
                nums_in_row = 1
        
            else:

                copy_array[i] = HEADER + \
                    OKGREEN + copy_array[i] + DEFAULT + "\t"
                nums_in_row += 1

        copy_array = ''.join(copy_array)
        return copy_array  # LISTA

    def help(self): #Get all commands

        manager = Apache2Manager()
        commands = manager.commands()
        grid = self.grid
        grid_commands = []

        for x in range(len(commands)):

            command = str(x) + ") " + CYAN + commands[x] + ENDC
            grid_commands.append(command)

        print(grid(grid_commands))

class Get():

    manager = Apache2Manager()
    messages = Messages()
    helper = Helper()

    def disabled_sites(self): #Get disable sites

        available_sites = self.available_sites()
        enabled_sites = self.enabled_sites()
        disabled_sites = []

        sites = [item for item in available_sites if item not in enabled_sites]

        for x in range(len(sites)):

            prefix = FAIL
            disabled_site = str(x) + ") " + prefix + sites[x] + ENDC
            disabled_sites.append(disabled_site)

        self.messages.clear_console()

        return sites

    def enabled_sites(self): #Get enabled sites

        enabled_sites_list = os.listdir(self.manager.enabled_sites_path)
        sorted_enabled_sites_list = sorted(enabled_sites_list)
        enabled_sites = self.helper.grid(sorted_enabled_sites_list)
        self.messages.clear_console()

        return sorted_enabled_sites_list

    def available_sites(self): #Get available sites

        available_sites_list = os.listdir(self.manager.available_sites_path)
        sorted_available_sites_list = sorted(available_sites_list)
        available_sites = self.helper.grid(sorted_available_sites_list)
        self.messages.clear_console()

        return sorted_available_sites_list

    def all_sites(self): #If site enabled: green else red and prints all

        global sites
        global available_sites
        global enabled_sites

        available_sites = self.available_sites()
        enabled_sites = self.enabled_sites()
        sites = available_sites + list(set(enabled_sites) - set(available_sites))
        sites_grid = []

        for x in range(len(sites)):

            if available_sites[x] not in enabled_sites: #If VHost is not enabled uses the RED color...

                prefix = FAIL
                site = HEADER + str(x) + ") " + prefix + available_sites[x] + ENDC
                sites_grid.append(site)

            else: #... else GREEN

                prefix = OKGREEN
                site = HEADER + str(x) + ") " + prefix + available_sites[x] + ENDC
                sites_grid.append(site)

        self.messages.clear_console()

        print(self.helper.grid(sites_grid))
        print()

    def php_versions(self): #Get all PHP versions installed

        php_versions = []

        for file in os.listdir("/etc/init.d"): #Lists all files in /etc/init.d

            if file.endswith("-fpm"):

                php_versions.append(file)
    
        php_versions = sorted(php_versions) #Sorts the PHP Versions

        return php_versions

    def url(self, vhost): #Gets the url from the VHost conf file

        vhost = open(vhost).read()
        url = re.search(self.manager.regex_url, vhost).group(0)
        url = 'http://' + url

        return url

    def docroot(self, vhost): #Gets the docroot from the VHost conf file

        vhost = open(vhost).read()
        docroot = re.search(self.manager.regex_docroot, vhost).group(0)

        return docroot

    def php(self, vhost): #Gets the PHP version from the VHost conf file

        vhost = open(vhost).read()
        php = re.search(self.manager.regex_php, vhost).group(0)

        return php

class Site():

    manager = Apache2Manager()
    messages = Messages()
    helper = Helper()
    get = Get()

    def enable(self, vhost = ''): #Enable site

        if vhost != '': #If a vhost is specified as argument...
                    
            site = vhost
            if not vhost.startswith(self.manager.available_sites_path + '/'): #...writes before the vhost the /etc/apache2/sites-available/ path

                vhost = self.manager.available_sites_path + '/' + vhost
                enable_command = "sudo a2ensite {0}".format(site)
                reload_command = "sudo systemctl reload apache2"
                subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

        else:

            enable_input = ''
            while enable_input == '':

                try:

                    available_sites = self.get.available_sites()
                    disabled_sites = self.get.disabled_sites()
                    enabled_sites = self.get.enabled_sites()
                    self.get.all_sites()

                    try:

                        site_to_enable = int(input("\nVHost to enable: "))

                    except (KeyboardInterrupt, EOFError):

                        self.messages.clear_console()
                        Cli().main_menu()

                    enable_command = "sudo a2ensite {0}".format(available_sites[site_to_enable])
                    reload_command = "sudo systemctl reload apache2"
                    
                    if available_sites[site_to_enable] in enabled_sites: #If VHost is enabled does not enable it...

                        self.messages.error("Site {2}{0}{1}{2}{3} already enabled!".format(CYAN, available_sites[site_to_enable], ENDC, FAIL))
                        enable_input = ''

                    else: #... else enables it

                        subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                        self.messages.correct("\nSite {2}{0}{1}{2}{3} successfully enabled!".format(CYAN, available_sites[site_to_enable], ENDC, OKGREEN))
                        subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                        self.messages.correct("Service Apache2 successfully reloaded!\n")
                        enable_input = '_'
            
                except (ValueError, IndexError):

                    self.messages.error("Value not allowed!")
                    enable_input = ''

    def disable(self, vhost = ''): #Disable site

        if vhost != '': #If a vhost is specified as argument...

            site = vhost

            if not vhost.startswith(self.manager.available_sites_path + '/'): #...writes /etc/apache2/sites-available/ before

                vhost = self.manager.available_sites_path + '/' + vhost
                disable_command = "sudo a2dissite {0}".format(site)
                reload_command = "sudo systemctl reload apache2"
                subprocess.call(disable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

        else:

            disable_input = ''
            while disable_input == '':

                try:
    
                    disabled_sites = self.get.disabled_sites()
                    enabled_sites = self.get.enabled_sites()
                    available_sites = self.get.available_sites()

                    self.get.all_sites()

                    try:

                        site_to_disable = int(input("\nVHost to disable: "))

                    except (KeyboardInterrupt, EOFError, ValueError):

                        self.messages.error("Value not allowed!")
                        self.messages.clear_console()
                        Cli().main_menu()

                    enable_command = "sudo a2dissite {0}".format(available_sites[site_to_disable])
                    reload_command = "sudo systemctl reload apache2"

                    if available_sites[site_to_disable] not in enabled_sites:
                    
                        self.messages.error("Site {2}{0}{1}{2}{3} already disabled!".format(CYAN, available_sites[site_to_disable], ENDC, FAIL))
                        disable_input = ''

                    else:
                    
                        subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                        self.messages.correct("\nSite {2}{0}{1}{2}{3} successfully disabled!".format(CYAN, available_sites[site_to_disable], ENDC, FAIL))
                        subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                        self.messages.correct("Service Apache2 successfully reloaded!\n")
                        disable_input = '_'

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

class Change():

    manager = Apache2Manager()
    commands = manager.commands()
    messages = Messages()
    helper = Helper()
    get = Get()
    site = Site()
    remove = Delete()
    add = Add()


    def url(self, new_url, vhost):

        vhost = self.manager.available_sites_path + '/' + vhost or ''

        with open(vhost, 'r') as vhost_conf:

            new_vconf = vhost_conf.read()
            old_url = re.search(self.manager.regex_url, new_vconf).group(0)

        with open(vhost, 'w') as vhost_conf:

            new_vconf = re.sub(self.manager.regex_url, new_url, new_vconf)
            vhost_conf.write(new_vconf)

        self.remove.from_etc_hosts(old_url)
        self.add.hosts_entry(new_url)
        self.messages.correct("Successfully replaced {3}{0}{4} URL from {3}{1}{4} with {3}{2}{4}!".format(vhost, old_url, new_url, CYAN, ENDC))

    def docroot(self, new_docroot_path, vhost):

        vhost = self.manager.available_sites_path + '/' + vhost or ''

        with open(vhost, 'r') as vhost_conf:

            new_vconf = vhost_conf.read()
            old_docroot_path = re.search(self.manager.regex_docroot, new_vconf).group(0)

        with open(vhost, 'w') as vhost_conf:

            new_vconf = re.sub(self.manager.regex_docroot, new_docroot_path, new_vconf)
            vhost_conf.write(new_vconf)

        mv_command = 'mv {0} {1}'.format(old_docroot_path, new_docroot_path)
        move(old_docroot_path, new_docroot_path)
        self.messages.correct("Successfully replaced {2}{0}{3} docroot with {2}{1}{3}!".format(vhost, new_docroot_path, CYAN, ENDC))

    def php(self, new_php_version, vhost):

        vhost = self.manager.available_sites_path + '/' + vhost or ''

        with open(vhost, 'r') as vhost_conf:

            new_vconf = vhost_conf.read()
            old_php_version = re.search(self.manager.regex_php, new_vconf).group(0)

        with open(vhost, 'w') as vhost_conf:

            new_vconf = re.sub(self.manager.regex_php, new_php_version, new_vconf)
            vhost_conf.write(new_vconf)

        self.messages.correct("Successfully replaced {3}{0}{4} PHP version from {3}{1}{4} to {3}{2}{4}!".format(vhost, old_php_version, new_php_version, CYAN, ENDC))
class VHost():

    manager = Apache2Manager()
    messages = Messages()
    commands = manager.commands()
    helper = Helper()
    get = Get()
    site = Site()
    remove = Delete()
    change = Change()
    add = Add()

    def create(self): #Create vhost

        try:
            
            name = input("Site name: ").replace(" ", "").lower()
            print('\n')

        except (KeyboardInterrupt, EOFError):

            self.messages.clear_console()
            Cli().main_menu()

        url = name + self.manager.domain 
        docroot = "/var/www/{0}".format(name)
        conf_file = "/etc/apache2/sites-available/{0}.conf".format(name)
        conf_file_name = conf_file[29:len(conf_file)]
        php_version = self.get.php_versions()

        for x in range(len(php_version)):

            print(OKBLUE + str(x) + ") " + ENDC + CYAN + php_version[x] + ENDC)

        try:
            
            php_version_input = int(input("\nPHP Version: "))

        except (KeyboardInterrupt, EOFError):

            self.messages.clear_console()
            Cli().main_menu()

        php_fpm = php_version[php_version_input]

        self.messages.warning("\nCreating the document root: {0}".format(docroot))
        self.add.docroot(docroot)
        self.messages.warning("\nFixing the permissions for the document root: {0}".format(docroot))
        chown(docroot, self.manager.user, self.manager.www_data_group)
        self.messages.warning("\nCreating the Apache2 VHost file: {0}".format(conf_file_name))

        copyfile(self.manager.template_vhost, conf_file)
        replace("template.email", self.manager.email, conf_file)
        replace("template.url", url, conf_file)
        replace("template.docroot", docroot, conf_file)
        replace("phpversion", php_fpm, conf_file)

        self.messages.warning("\nCreating the new {0} Virtual Host with document root: {1}".format(url, docroot))
        self.add.hosts_entry(url)
        self.messages.warning("Adding $url to the /etc/hosts file...")

        with open(docroot + "/index.php", "w") as phpinfo:

                    phpinfo.write("<?php phpinfo(); ?>") #PHPINFO
                    phpinfo.close()

        try:
            
            enable_prompt = input("Do you want to enable {2}{0}{1}? [Y,n]: ".format(url, ENDC, CYAN)).lower()

        except (KeyboardInterrupt, EOFError):

            self.messages.clear_console()
            Cli().main_menu()

        if enable_prompt in ['', 'y']:

            self.site.enable(conf_file_name)

        else:

            self.messages.warning("OK but don't forget to enable the vhost for using it :p ")

        self.messages.correct("\nYou can now browse to your Virtual Host at http://{0}".format(url))

    def delete(self): #Delete vhost

        self.messages.warning("WARNING! IF YOU DELETE A VHOST YOU WILL LOST ANY DATA RELATED WITH IT.")
        user_input = ''

        while user_input == '':

            try:
                
                user_confirmation = input("ARE YOU SURE YOU WANT TO PROCEED? [y,N]: ").lower()

            except (KeyboardInterrupt, EOFError):

                self.messages.clear_console()
                Cli().main_menu()

            if user_confirmation not in ["y", "N", '']:

                self.messages.error("Answer not valid. Please retry!")
                user_input = ''

            if user_confirmation in ['', 'n']:

                self.messages.warning("Action cancelled")

            if user_confirmation in ["y"]:

                self.get.all_sites()

                try:

                    site_input = ''
                    while site_input == '':
                
                        site_to_destroy = int(input("Delete VHost: "))
                        vhost_conf = self.manager.available_sites_path + '/' + sites[site_to_destroy]
                        delete_www_path = self.get.docroot(vhost_conf)
                        url = self.get.url(vhost_conf)

                        if sites[site_to_destroy] in enabled_sites:
                        
                            self.messages.warning("Site {0} is currently enabled. Disabling it...".format(url))
                            self.site.disable(sites[site_to_destroy])
                            site_input = '_'
                            
                        else:
                            
                            self.messages.correct("Site {0} is already disabled. Nothing to do here...".format(url))
                            site_input = '_'
                    
                except ValueError:
                
                    self.messages.error("Value not allowed. Please retry again!")
                    site_input = ''

                try:

                    etc_hosts_input = ''
                    while etc_hosts_input == '':

                        remove_etc_hosts = input("Remove {0} from the /etc/hosts file? [Y,n]: ".format(url)).lower()

                        if remove_etc_hosts not in ["y", "n", '']:
                        
                            self.messages.error("Answer not valid. Please retry!")
                            etc_hosts_input = ''

                        if remove_etc_hosts in ['', 'y']:
                        
                            self.remove.from_etc_hosts(url)
                            etc_hosts_input = '_'
                        
                        else:
                        
                            etc_hosts_input = '_'

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                try:

                    www_input = ''
                    while www_input == '':
                    
                        remove_www = input("Remove the content of {0} from /var/www? [y,N]: ".format(url)).lower()

                        if remove_www not in ["y", "n", '']:

                            self.messages.error("Answer not valid. Please retry!")
                            www_input = ''

                        if remove_www in ['y']:

                            self.remove.var_www(url, delete_www_path)
                            www_input = '_'

                        else:
                            
                            www_input = '_'

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                try:

                    vhost_input = ''
                    while vhost_input == '':
                    
                        remove_vhost_conf = input("Remove the vhost configuration file for {0}? [y,N]: ".format(url)).lower()
                        if remove_vhost_conf not in ["y", "n"]:
                        
                            self.messages.error("Answer not valid. Please retry!")

                        if remove_vhost_conf in ['y']:
                        
                            self.remove.vhost_conf(url, vhost_conf)
                            self.messages.correct("Site {0} successfully destroyed, good job bro'".format(url))
                            self.messages.clear_console()
                            vhost_input = '_'

                        else:

                            vhost_input = '_'

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                Cli().main_menu()

            
    def edit(self, vhost = ''):

        vhost = vhost or ''
        self.messages.warning("Be careful editing those parameters, they can break your vhost!")
        user_input = ''

        while user_input == '':

            try:
                
                user_confirmation = input("ARE YOU SURE YOU WANT TO PROCEED? [y,N]: ").lower()

            except (KeyboardInterrupt, EOFError):

                self.messages.clear_console()
                Cli().main_menu()

            if user_confirmation not in ["y", "n", '']:

                self.messages.error("Answer not valid. Please retry!")
                user_input = ''

            if user_confirmation in ['', 'n']:

                self.messages.warning("Action cancelled")

                Cli().main_menu()

            if user_confirmation in ["y"]:

                disabled_sites = self.get.disabled_sites()
                enabled_sites = self.get.enabled_sites()
                available_sites = self.get.available_sites()
                self.get.all_sites()

                try:
                    
                    site_to_edit = int(input("\nEdit VHost: "))

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                vhost = sites[site_to_edit]

                if available_sites[site_to_edit] not in enabled_sites:

                    self.messages.error("Site {2}{0}{1}{2}{3} already disabled!".format(CYAN, sites[site_to_edit], ENDC, FAIL))

                else:

                    self.site.disable(sites[site_to_edit])

                url = Show().get.url(self.manager.available_sites_path + '/' + sites[site_to_edit])

                try:

                    url_input = ''
                    while url_input == '':
                    
                        edit_url_prompt = input("Change {1}{0}{2} URl? [y,N]: ".format(url, CYAN, ENDC)).lower()
                        if edit_url_prompt not in ["y", "n", ""]:

                            self.messages.error("Answer not valid. Please retry!")
                            url_input = ''
                        
                        if edit_url_prompt in ["y"]:

                            try:

                                new_url = input("New URL: ").lower()

                            except (KeyboardInterrupt, EOFError):
                            
                                self.messages.clear_console()
                                Cli().main_menu()

                            self.change.url(new_url, sites[site_to_edit])
                            self.site.enable(sites[site_to_edit])
                            url_input = '_'
                
                        else:

                            url_input = '_'

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                    
                docroot_input = ''
                while docroot_input == '':

                    try:
                        
                        edit_docroot_prompt = input("\nChange {0} docroot? [y,N]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError):

                        self.messages.clear_console()
                        Cli().main_menu()

                    if edit_docroot_prompt not in ['', 'y', 'n']:

                        self.messages.error("Answer not valid. Please retry!")
                        docroot_input = ''                        

                    if edit_docroot_prompt in ['y']:

                        try:
                            
                            newdocroot = input("New docroot: [/var/www/]: ")

                        except (KeyboardInterrupt, EOFError):

                            self.messages.clear_console()
                            Cli().main_menu()

                        new_docroot = '/var/www/{0}'.format(newdocroot)
                        self.change.docroot(new_docroot, vhost)
                        docroot_input = '_'

                    else:

                        docroot_input = '_'

                php_prompt = ''

                while php_prompt == '':

                    try:
                        
                        edit_php_prompt = input("\nChange {0} PHP version? [y,N]: ".format(url)).lower()

                        if edit_php_prompt not in ['', 'y', 'n']:  # Check for command

                            self.messages.error("Answer not valid. Please retry!")
                            php_prompt = ''

                        if edit_php_prompt in ['y']:

                            php_version = self.get.php_versions()
                            print()

                            for x in range(len(php_version)):

                                print(OKBLUE + str(x) + ") " + ENDC + CYAN + php_version[x] + ENDC)

                            try:

                                new_php_input = ''
                                while new_php_input == '':

                                    new_php_version = int(input("\nPHP Version: "))

                                    try:

                                        php_fpm = php_version[new_php_version]
                                        self.change.php(php_fpm, sites[site_to_edit])
                                        php_prompt = '_'
                                        new_php_input = '_'
                                    
                                    except IndexError:

                                        self.messages.error("Version not found!")
                                        new_php_input = ''

                            except (KeyboardInterrupt, EOFError):

                                self.messages.clear_console()
                                Cli().main_menu()

                        else:

                            php_prompt = '_'

                    except (KeyboardInterrupt, EOFError):

                        self.messages.clear_console()
                        Cli().main_menu()

                self.site.disable(sites[site_to_edit])
                self.site.enable(sites[site_to_edit])

                Cli().main_menu()

class Show():

    def __init__(self):


        self.manager = Apache2Manager()
        self.commands = self.manager.commands()
        self.messages = Messages()
        self.helper = Helper()
        self.get = Get()
        self.site = Site()
        self.remove = Delete()
        self.vhost = VHost()
        self.change = Change()

    def all_info(self, vhost = ''):

        if not vhost.startswith(self.manager.available_sites_path + '/'):

            vhost = self.manager.available_sites_path + '/' + vhost

        URL = self.get.url(vhost)
        docroot = self.get.docroot(vhost)
        php_version = self.get.php(vhost)
        print_template = """\nURL: {3}{0}{4}\nDocroot: {3}{1}{4}\nPHP Version: {3}{2}{4}\n""".format(URL, docroot, php_version, CYAN, ENDC)

        print(print_template)

    def info(self):

        site_input = ''
        self.get.all_sites()

        try:

            while site_input == '':

                try:

                    site_to_show = int(input("\nVHost info: "))

                except (KeyboardInterrupt, EOFError):

                    self.messages.clear_console()
                    Cli().main_menu()

                self.all_info(sites[site_to_show])
                site_input = '_'
        
        except (IndexError, ValueError):
            
            self.messages.error("Value not accepted, please retry again!")
            site_input = ''

class Cli():

    def __init__(self):

        self.manager = Apache2Manager()
        self.commands = self.manager.commands()
        self.messages = Messages()
        self.helper = Helper()
        self.get = Get()
        self.site = Site()
        self.remove = Delete()
        self.vhost = VHost()
        self.change = Change()
        self.show = Show()

    def main_menu(self): #Main menu

        shell_prompt = ""

        while shell_prompt == "":

            try:
                
                command = input(">>> ").lower().replace(" ", "")  # Shell input

                if command not in self.commands:  # Check for command

                    self.messages.command_not_found(command)

                if command in ["quit", "exit", "close"]:

                    print("Bye Bye!")
                    exit()

                if command in ["list"]:

                    self.get.all_sites()

                if command in ["add", "create", "new"]:

                    self.vhost.create()

                if command in ["disable", 'dis']:

                    self.site.disable()

                if command in ["enable", 'ena']:

                    self.site.enable()

                if command in ["remove", "delete", "destroy", 'rem', 'del']:

                    self.vhost.delete()

                if command in ["edit"]:

                    self.vhost.edit()

                if command in ["?", "help"]:

                    self.helper.help()

                if command in ["show", 'info']:

                    self.show.info()

            except (KeyboardInterrupt, EOFError):

                self.messages.clear_console()
                Cli().main_menu()

if __name__ == "__main__":

    Cli().main_menu()
