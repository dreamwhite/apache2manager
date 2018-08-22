#!/usr/bin/python3
# -*- coding: utf-8 -*-

# STRUCTURE: THE VHOST ENABLED ARE IN THE DIRECTORY /etc/apache2/sites-enabled and follows the format $sitename.conf
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
from pysed import *

class Apache2Manager():

    sites = []
    php_version = []

    FNULL = open(os.devnull, 'w')
    
    def __init__(self):

        if not os.geteuid() == 0:
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
        global sites
        global php_version

    def commands(self):

        commands = [

            "add",
            "close",
            "create",
            "delete",
            "destroy",
            "disable",
            "enable",
            "edit",
            "exit",
            "help",
            "list",
            "new",
            "quit",
            "remove",
            "show",

        ] #Commands

        return commands


class Messages(): #Custom messages

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

        subprocess.call("sudo rm {0}".format(vhost), shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
        self.messages.correct("VHost configuration file for {0} successfully deleted!".format(url))

class Helper():
    
    def grid(self, array): #Create grid

        copyArray = array[:]
        numsPerRow = 4
        numsInRow = 1

        for i in range(len(array)):

            if numsInRow % numsPerRow == 0:

                copyArray[i] = HEADER + \
                    OKGREEN + copyArray[i] + DEFAULT + "\n"
                numsInRow = 1
        
            else:

                copyArray[i] = HEADER + \
                    OKGREEN + copyArray[i] + DEFAULT + "\t"
                numsInRow += 1

        copyArray = ''.join(copyArray)
        return copyArray  # LISTA

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

        sites = available_sites + list(set(enabled_sites) - set(available_sites)) #LIST

        sites_grid = []

        for x in range(len(sites)):

            if available_sites[x] not in enabled_sites:

                prefix = FAIL

                site = HEADER + str(x) + ") " + prefix + available_sites[x] + ENDC

                sites_grid.append(site)

            else:

                prefix = OKGREEN

                site = HEADER + str(x) + ") " + prefix + available_sites[x] + ENDC

                sites_grid.append(site)

        self.messages.clear_console()

        print(self.helper.grid(sites_grid))

    def php_versions(self): #Get all PHP versions installed

        php_versions = []

        for file in os.listdir("/etc/init.d"):

            if file.endswith("-fpm"):

                php_versions.append(file)
    
        php_versions = sorted(php_versions)

        return php_versions


class Site():

    manager = Apache2Manager()
    messages = Messages()
    helper = Helper()
    get = Get()

    def enable(self, site = ''): #Enable site


        site = site[:-5] or ''

        if site != '':

            enable_command = "sudo a2ensite {0}".format(site)
            reload_command = "sudo systemctl reload apache2"
            subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
            subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

        else:

            available_sites = self.get.available_sites()
            disabled_sites = self.get.disabled_sites()
            enabled_sites = self.get.enabled_sites()
            self.get.all_sites()

            site_to_enable = int(input("Site to enable: "))

            enable_command = "sudo a2ensite {0}".format(available_sites[site_to_enable])

            reload_command = "sudo systemctl reload apache2"

            if available_sites[site_to_enable] in enabled_sites:

                self.messages.error("Site {2}{0}{1}{2}{3} already enabled!".format(CYAN, available_sites[site_to_enable], ENDC, FAIL))

            else:

                subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                self.messages.correct("Site {2}{0}{1}{2}{3} successfully enabled!".format(CYAN, available_sites[site_to_enable], ENDC, OKGREEN))
                subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                self.messages.correct("Service Apache2 successfully reloaded!")


    def disable(self, site = ''): #Disable site

        site = site[:-5] or ''

        if site != '':

            disable_command = "sudo a2dissite {0}".format(site)
            reload_command = "sudo systemctl reload apache2"
            subprocess.call(disable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
            subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

        else:
    
            disabled_sites = self.get.disabled_sites()
            enabled_sites = self.get.enabled_sites()
            available_sites = self.get.available_sites()
            self.get.all_sites()

            try:
                site_to_disable = int(input("Site to disable: "))

                enable_command = "sudo a2dissite {0}".format(available_sites[site_to_disable])
                reload_command = "sudo systemctl reload apache2"

                if available_sites[site_to_disable] not in enabled_sites:

                    self.messages.error("Site {2}{0}{1}{2}{3} already disabled!".format(CYAN, available_sites[site_to_disable], ENDC, FAIL))

                else:

                    self.messages.clear_console()
                    subprocess.call(enable_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                    self.messages.correct("Site {2}{0}{1}{2}{3} successfully disabled!".format(CYAN, available_sites[site_to_disable], ENDC, FAIL))
                    subprocess.call(reload_command, shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)
                    self.messages.correct("Service Apache2 successfully reloaded!")

            except (KeyboardInterrupt, EOFError) as e:

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

    regex_url = "(?<=ServerName ).*(?=)"
    regex_docroot = "(?<=DocumentRoot ).*?(?=)"
    regex_directory = "(?<=<Directory ).*?(?=\/>)"
    regex_php = """(?<=SetHandler "proxy:unix:\/var\/run\/php\/).*(?=.sock\|fcgi:\/\/localhost\/)"""

    def url(self, newurl, vhost):

        vhost = self.manager.available_sites_path + '/' + vhost or ''

        with open(vhost, 'r') as vhost_conf:

            new_vconf = vhost_conf.read()
            old_url = re.search(self.regex_url, new_vconf).group(0)
            print(old_url)

        with open(vhost, 'w') as vhost_conf:

            new_vconf = re.sub(self.regex_url, newurl, new_vconf)
            vhost_conf.write(new_vconf)

        self.remove.from_etc_hosts(old_url)

        with open(self.manager.hosts_file, 'a') as hosts:

            hosts.write("127.0.0.1       {0}".format(newurl))
        
        self.messages.correct("Successfully replaced {3}{0}{4} URL from {3}{1}{4} with {3}{2}{4}!".format(vhost, old_url, newurl, CYAN, ENDC))

    def docroot(self, newdocroot, vhost):

        newdocroot = '/var/www/{0}'.format(newdocroot)

        old_docroot = re.search(self.regex_docroot, vhost).group(0)

        new_docroot = re.sub(self.regex_docroot, newdocroot, vhost)

        subprocess.call("mv {0}".format(newdocroot), shell=True, stdout=self.manager.FNULL, stderr=subprocess.STDOUT)

        self.messages.correct("Successfully replaced {2}{0}{3} docroot with {2}{1}{3}!".format(vhost, newdocroot, CYAN, ENDC))

    def php(self, new_php_version, vhost):

        vhost = self.manager.available_sites_path + '/' + vhost

        with open(vhost, 'r') as vhost_conf:

            new_vconf = vhost_conf.read()
            old_php_version = re.search(self.regex_php, new_vconf).group(0)

        with open(vhost, 'w') as vhost_conf:

            new_vconf = re.sub(self.regex_php, new_php_version, new_vconf)
        
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

    def create(self): #Create vhost
        

        try:
            
            name = input("Site name: ").lower()

        except (KeyboardInterrupt, EOFError) as e:

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

        except (KeyboardInterrupt, EOFError) as e:

            self.messages.clear_console()
            Cli().main_menu()

        php_fpm = php_version[php_version_input]



        if os.path.exists(docroot):
            docroot += "_1"

        self.messages.warning("\nCreating the document root: {0}".format(docroot))
        os.mkdir(docroot)
        self.messages.warning("\nFixing the permissions for the document root: {0}".format(docroot))

        chown(docroot, self.manager.user, self.manager.www_data_group)
        self.messages.warning("\nCreating the Apache2 VHost file: {0}".format(conf_file_name))

        copyfile(self.manager.template_vhost, conf_file)
        replace("template.email", self.manager.email, conf_file)
        replace("template.url", url, conf_file)
        replace("template.docroot", docroot, conf_file)
        replace("phpversion", php_fpm, conf_file)

        self.messages.warning("\nCreating the new {0} Virtual Host with document root: {1}".format(url, docroot))

        with open(self.manager.hosts_file, 'a') as hosts:

            hosts.write("\r127.0.0.1       {0}".format(url))
        
        self.messages.warning("Adding $url to the /etc/hosts file...")


        with open(docroot + "/index.php", "w") as phpinfo:

                    phpinfo.write("<?php phpinfo(); ?>") #PHPINFO
                    phpinfo.close()


        try:
            
            enable_prompt = input("Do you want to enable {2}{0}{1}? [Y,n]: ".format(url, ENDC, CYAN)).lower()

        except (KeyboardInterrupt, EOFError) as e:

            self.messages.clear_console()
            Cli().main_menu

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

            except (KeyboardInterrupt, EOFError) as e:

                self.messages.clear_console()
                Cli().main_menu

            if user_confirmation not in ["y", "N", '']:

                self.messages.error("Answer not valid. Please retry!")

                user_input = ''

            if user_confirmation in ['', 'n']:

                self.messages.warning("Action cancelled")

            if user_confirmation in ["y"]:

                self.get.all_sites()

                try:
                    
                    site_to_destroy = int(input("Which vhost do you want to delete?: "))

                except (KeyboardInterrupt, EOFError) as e:

                    self.messages.clear_console()
                    Cli().main_menu

                vhost_conf = self.manager.available_sites_path + '/' + sites[site_to_destroy]

                domain_subfix = sites[site_to_destroy][:-5]

                delete_www_path = '/var/www/{0}'.format(domain_subfix)

                url = domain_subfix + self.manager.domain

                if sites[site_to_destroy] in enabled_sites:

                    self.messages.warning("Site {0} is currently enabled. Disabling it...".format(url))
                    self.site.disable(sites[site_to_destroy])

                else:

                    self.messages.correct("Site {0} is already disabled. Nothing to do here...".format(url))

                etc_hosts_input = ''

                while etc_hosts_input == '':

                    try:
                        
                        remove_from_etc_hosts_prompt = input("Remove {0} from the /etc/hosts file? [Y,n]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu

                    if remove_from_etc_hosts_prompt not in ["y", "n"]:

                        self.messages.error("Answer not valid. Please retry!")
                        etc_hosts_input = ''

                    if user_confirmation in ['', 'y']:

                        self.remove.from_etc_hosts(url)
                        etc_hosts_input = '_'

                www_input = ''

                while www_input == '':

                    try:
                        
                        remove_www = input("Remove the content of {0} from /var/www? [y,N]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu

                    if remove_www not in ["y", "n"]:

                        self.messages.error("\nAnswer not valid. Please retry!")

                    if remove_www in ['y']:

                        self.remove.var_www(url, delete_www_path)
                        www_input = '_'

                vhost_input = ''

                while vhost_input == '':

                    try:
                        
                        remove_vhost_conf = input("Remove the vhost configuration file for {0}? [y,N]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu

                    if remove_vhost_conf not in ["y", "n"]:

                        self.messages.error("\nAnswer not valid. Please retry!")

                    if remove_vhost_conf in ['y']:

                        self.remove.vhost_conf(url, vhost_conf)
                        self.messages.correct("Site {0} successfully destroyed, good job bro'".format(url))
                        self.messages.clear_console()
                        vhost_input = '_'

                Cli().main_menu()
            
    def edit(self, vhost = ''):

        vhost = vhost or ''

        self.messages.warning("Be careful editing those parameters, they can break your vhost!")

        user_input = ''

        while user_input == '':

            try:
                
                user_confirmation = input("ARE YOU SURE YOU WANT TO PROCEED? [y,N]: ").lower()

            except (KeyboardInterrupt, EOFError) as e:

                self.messages.clear_console()
                Cli().main_menu

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
                    
                    site_to_edit = int(input("Which vhost do you want to edit?: "))

                except (KeyboardInterrupt, EOFError) as e:

                    self.messages.clear_console()
                    Cli().main_menu()

                vhost = sites[site_to_edit]

                if available_sites[site_to_edit] not in enabled_sites:

                    self.messages.error("Site {2}{0}{1}{2}{3} already disabled!".format(CYAN, sites[site_to_edit], ENDC, FAIL))

                else:

                    self.site.disable(sites[site_to_edit])

                vhost_conf_file = self.manager.available_sites_path + '/' + vhost
                

                with open(vhost_conf_file, 'r') as f:

                    vhost_conf = f.read()

                domain_subfix = sites[site_to_edit][:-5]

                url = domain_subfix + self.manager.domain
        
                url_input = ''

                while url_input == '':

                    try:
                        
                        edit_url_prompt = input("Change {1}{0}{2} URl? [y,N]: ".format(url, CYAN, ENDC)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu

                    if edit_url_prompt not in ["y", "n", ""]:

                        self.messages.error("Answer not valid. Please retry!")
                        url_input = ''

                    if edit_url_prompt in ["y"]:

                        try:
                            
                            new_url = input("New URL: ").lower()

                        except (KeyboardInterrupt, EOFError) as e:

                            self.messages.clear_console()
                            Cli().main_menu

                        self.change.url(new_url, sites[site_to_edit])

                        self.site.enable(sites[site_to_edit])

                        url_input = '_'
                    
                    else:

                        url_input = '_'

                docroot_input = ''

                while docroot_input == '':

                    try:
                        
                        edit_docroot_prompt = input("Change {0} docroot? [y,N]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu

                    if edit_docroot_prompt not in ['', 'y', 'n']:

                        self.messages.error("Answer not valid. Please retry!")
                        docroot_input = ''                        

                    if edit_docroot_prompt in ['y']:

                        try:
                            
                            newdocroot = input("New docroot: [/var/www/]: ")

                        except (KeyboardInterrupt, EOFError) as e:

                            self.messages.clear_console()
                            Cli().main_menu()

                        new_docroot = '/var/www/{0}'.format(newdocroot)
                        self.change.docroot(new_docroot, vhost_conf_file)
                        docroot_input = '_'

                    else:

                        docroot_input = '_'

                php_prompt = ''

                while php_prompt == '':

                    try:
                        
                        edit_php_prompt = input("Change {0} PHP version? [y,N]: ".format(url)).lower()

                    except (KeyboardInterrupt, EOFError) as e:

                        self.messages.clear_console()
                        Cli().main_menu()

                    if edit_php_prompt not in ['', 'y', 'n']:  # Check for command

                        self.messages.error("Answer not valid. Please retry!")
                        php_prompt = ''

                    if edit_php_prompt in ['y']:

                        php_version = self.get.php_versions()

                        for x in range(len(php_version)):

                            print(OKBLUE + str(x) + ") " + ENDC + CYAN + php_version[x] + ENDC)

                        try:
                            
                            new_php_version = int(input("PHP Version: "))

                        except (KeyboardInterrupt, EOFError) as e:

                            self.messages.clear_console()
                            Cli().main_menu()

                        php_fpm = php_version[new_php_version]
                        self.change.php(php_fpm, sites[site_to_edit])
                        php_prompt = '_'

                    else:

                        php_prompt = '_'

                self.site.disable(sites[site_to_edit])
                self.site.enable(sites[site_to_edit])

                Cli().main_menu()
                

class Cli():

    manager = Apache2Manager()
    commands = manager.commands()
    messages = Messages()
    helper = Helper()
    get = Get()
    site = Site()
    remove = Delete()
    vhost = VHost()
    change = Change()

    def main_menu(self): #Main menu

        shell_prompt = ""

        while shell_prompt == "":

            try:
                
                command = input(">>> ").lower()  # Shell input

                if command not in self.commands:  # Check for command

                    self.messages.command_not_found(command)

                if command in ["quit", "exit", "close"]:

                    print("Bye Bye!")
                    exit()

                if command in ["list", "show", "enabled"]:

                    self.get.all_sites()

                if command in ["add", "create", "new"]:

                    self.vhost.create()

                if command in ["disable"]:

                    self.site.disable()

                if command in ["enable"]:

                    self.site.enable()

                if command in ["remove", "delete", "destroy"]:

                    self.vhost.delete()

                if command in ["edit"]:

                    self.vhost.edit()

                if command in ["?", "help"]:

                    self.helper.help()

            except (KeyboardInterrupt, EOFError) as e:

                self.messages.clear_console()
                Cli().main_menu()

if __name__ == "__main__":

    Cli().main_menu()
