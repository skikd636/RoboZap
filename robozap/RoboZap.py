import os
import ntpath
import tarfile
from zapv2 import ZAPv2 as ZAP
import time
import subprocess
from robot.api import logger
import base64
import uuid
import glob
import json
import requests
from datetime import datetime
from six import binary_type
from sys import platform

EXT = '.bat' if platform == 'win32' else '.sh'

def write_report(file_path, report):
    with open(file_path, mode='wb') as f:
        if not isinstance(report, binary_type):
            report = report.encode('utf-8')

        f.write(report)


class RoboZap(object):
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, proxy, port):
        """
        ZAP Library can be imported with one argument

        Arguments:
            - ``proxy``: Proxy is required to initialize the ZAP Proxy at that location. This MUST include the port specification as well
            - ``port``: This is a portspecification that will be used across the suite


        Examples:

        | = Keyword Definition =  | = Description =  |

        | Library `|` RoboZap  | proxy | port |
        """
        self.zap = ZAP(proxies={"http": proxy, "https": proxy})
        self.port = port

        temp_name = str(uuid.uuid4())
        tmp_dir = os.getcwd()
        self.session = os.path.join(tmp_dir, temp_name)
        
        self.zap_exe = ""

    def start_headless_zap(self, path, extra_zap_params=[]):
        """
        Start OWASP ZAP without a GUI

        Examples:

        | start headless zap  |  path  |  extra_zap_params **optional**  |

        """
        self.zap_exe = os.path.join(path, f"zap{EXT}")
        params = [
            self.zap_exe, 
            '-daemon',
            '-newsession', str(self.session),
            '-port', str(self.port),
            '-config', 'database.recoverylog=false',
            '-config', 'api.disablekey=true',
            '-config', 'api.addrs.addr.name=.*',
            '-config', 'api.addrs.addr.regex=true']
        params.extend(extra_zap_params)   
        try:
            print(params)
            subprocess.Popen(params, stdout=open(os.devnull, "w"))
            time.sleep(10)
        except IOError:
            print("ZAP Path is not configured correctly")
            raise

    def start_gui_zap(self, path):
        """
        Start OWASP ZAP with a GUI

        Examples:

        | start gui zap  | path | port |

        """
        try:
            cmd = path + f"zap{EXT} -config api.disablekey=true -port {self.port}"
            print(cmd)
            subprocess.Popen(cmd.split(" "), stdout=open(os.devnull, "w"))
            time.sleep(10)
        except IOError:
            print("ZAP Path is not configured correctly")

    def zap_open_url(self, url):
        """
        Invoke URLOpen with ZAP

        Examples:

        | zap open url  | target |

        """
        self.zap.urlopen(url)
        time.sleep(4)

    def zap_define_context(self, contextname, url):
        """
        Add Target to a context and use the context to perform all scanning/spidering operations

        Examples:

        | zap define context  | contextname  | target |

        """
        regex = "{0}.*".format(url)
        context_id = self.zap.context.new_context(contextname=contextname)
        time.sleep(1)
        self.zap.context.include_in_context(contextname, regex=regex)
        time.sleep(5)
        return context_id


    def zap_exclude_from_context(self, contextname, regex):
        """
        Provide a way to exclude urls from spider and scanning using a regex.
          this is just a passthru.
        
        Examples:
        
        | zap exclude from context  |  contextname  |  regex  |
        
        """
        self.zap.context.exclude_from_context(contextname, regex)        

    def zap_include_in_context(self, contextname, regex):
        """
        Provide a way to include urls in spider and scanning using a regex.
          this is just a passthru.
        
        Examples:
        
        | zap include in context  |  contextname  |  regex  |
        
        """
        self.zap.context.include_in_context(contextname, regex)   
        
    def zap_get_context_info(self, contextname):
        """
        Get information about the context
        """
        
        return self.zap.context.context(contextname)

    def zap_add_session(self, target, sessionName):
        """
        Add a session so we can modify it later

        Examples:
        
        | zap add session | target  | sessionName  |
        
        """
        session_id = self.zap.httpsessions.create_empty_session(target, sessionName)
        time.sleep(2)
        return session_id

    def zap_set_active_session(self, target, sessionName):
        """
        Set the active session for a site
        
        Examples:
        
        | zap set active session | target  | sessionName  |
                
        """
        
        return self.zap.httpsessions.set_active_session(target, sessionName)
        
    def zap_get_active_session(self, target):
        """
        Get the active session for a site
        """
        
        return self.zap.httpsessions.active_session(target)        
        
    def zap_get_sessions(self, target):
        """
        Get all the sessions for a site
        """
        
        return self.zap.httpsessions.sessions(target)

    def zap_set_default_session_token(self, cookiename):
        """
        Set the default session tokens that will be used to manage sessions.
        
        Examples:
        
        | zap set default session token |  cookiename  |
                
        """

        self.zap.httpsessions.add_default_session_token(cookiename, True)
        
    def zap_set_session_token(self, target, cookiename):
        """
        Set the default session tokens that will be used to manage sessions.
        
        Examples:
        
        | zap set session token |  target  |  cookiename  |
                
        """

        self.zap.httpsessions.add_session_token(target, cookiename, True)        
        
    def zap_set_session_token_contains(self, target, cookiename, cookiedict):
        """
        Set a default session tokens based on matching a token using a regex
        
        Examples:
        
        | zap set session token contains |  target  |  cookiename  |  cookiedict  |
                
        """
        for key, value in cookiedict.items():
            if cookiename in key:
                self.zap.httpsessions.add_session_token(target, key, True)        
        
    def zap_add_anticsrf_token(self, tokenname):
        """
        Set the anticsrf token name
        
        Examples:
        
        | zap add anticsrf token |  tokenname  |
  
        """
        
        self.zap.acsrf.add_option_token(tokenname)
        
    def zap_get_session_tokens(self, target):
        """
        Get the session tokens for the default session for a site
        """
        
        return self.zap.httpsessions.session_tokens(target)
        
    def zap_import_urls(self, target):
        """
        Import a list of URLs into ZAP from a text file.  One url pre line.  
          File must be accessible from the ZAP command line.
        
        Examples:
        
        | zap import urls  |  target  |
        
        """    
        return self.zap.importurls.importurls(target)
        
    def zap_start_spider(self, contextname, url, maxchildren=None, recurse=None, subtreeonly=None):
        """
        Start ZAP Spider with ZAP's inbuilt spider mode

        Examples:

        | zap start spider  | contextname  | url |

        """
        try:

            spider_id = self.zap.spider.scan(url=url, contextname=contextname, maxchildren=maxchildren, recurse=recurse, subtreeonly=subtreeonly )
            time.sleep(2)
            return spider_id
        except Exception as e:
            print(e)

    def zap_spider_status(self, spider_id):
        """
        Fetches the status for the spider id provided by the user
        Examples:
        | zap spider status  | spider_id |
        """
        while int(self.zap.spider.status(spider_id)) < 100:
            logger.info(
                "Spider running at {0}%".format(int(self.zap.spider.status(spider_id)))
            )
            time.sleep(10)

    def zap_spider_urls(self):
        """
        Fetches the urls returned by the spider
        Examples:
        | zap spider urls  | 
        """
        return self.zap.spider.all_urls
        
        
    def zap_start_ajax_spider(self, contextname, url, inscope=None, subtreeonly=None):
        """
        Start ZAP AJAX Spider with ZAP.  Utilizes a browser.  Only works if it is installed and there is
          a configured browser working.  

        Examples:

        | zap start ajax spider  | contextname  | 

        """
        try:
            self.zap.ajaxSpider.scan(url=url, contextname=contextname, inscope=inscope, subtreeonly=subtreeonly )
            time.sleep(2)
        except Exception as e:
            print(e)

    def zap_ajax_spider_status(self):
        """
        Get the status of the ajax spider.  unitl it's done running.

        Examples:

        | zap ajax spider status  |

        """
        while (self.zap.ajaxSpider.status != 'stopped'):
            print('Ajax Spider is ' + self.zap.ajaxSpider.status)
            time.sleep(5)   
             

    def zap_set_threads_per_host(self, threads):
        """
        Set the number of threads to use per host.  Be default it is set to 2.
            Can speed up scanning but may overwhelm or logout the user.
        
        Examples:
        
        |  zap set threads per host  |  threads  |
        
        """
        
        self.zap.ascan.set_option_thread_per_host(threads)
        time.sleep(1)
        return self.zap.ascan.option_thread_per_host
        
    def zap_set_hosts_per_scan(self, hosts):
        """
        Set the number of hosts to scan at one time.  Be default it is set to 2.
            Can speed up scanning but may overwhelm or logout the user.
        
        Examples:
        
        |  zap set host per scan  |  hosts  |
        
        """
        
        self.zap.ascan.set_option_host_per_scan(hosts)        
        time.sleep(1)
        return self.zap.ascan.option_host_per_scan
        
    def zap_start_ascan(self, context, url, policy="Default Policy"):
        """
        Initiates ZAP Active Scan on the target url and context

        Examples:

        | zap start ascan  | context  | url |

        """
        try:
            scan_id = self.zap.ascan.scan(
                contextid=context, url=url, scanpolicyname=policy
            )
            time.sleep(2)
            return scan_id
        except Exception as e:
            print(e)

    def zap_scan_status(self, scan_id):
        """
        Fetches the status for the spider id provided by the user

        Examples:

        | zap scan status  | scan_id |

        """
        while int(self.zap.ascan.status(scan_id)) < 100:
            logger.info(
                "Scan running at {0}%".format(int(self.zap.ascan.status(scan_id)))
            )
            time.sleep(10)
            
    def zap_get_scanned_urls(self, contextname):
        """
        Gets the URLs that were scanned for the target
        
        Examples:
        
        | zap get scanned urls  | base_url  |
        
        """
        return self.zap.context.urls(contextname)
    
    def zap_spider_urls_to_file(self, target):
        """

        Fetches all the urls that were spidered from zself.zap.spider.all_urls and writes to text file.

        Examples:

        | zap spider urls to file  | target |

        """
        
        spider_urls = self.zap.spider.all_urls
        with open(target, "w") as f:
            for i in spider_urls:
                f.write(i)
                f.write('\r\n')
                
    def zap_all_urls_to_file(self, target, baseurl=None):
        """

        Fetches all the urls that are in scope, adding base url will filter on that.

        Examples:

        | zap spider urls to file  | target |

        """
        
        all_urls = self.zap.core.urls(baseurl)
        with open(target, "w") as f:
            for i in all_urls:
                f.write(i)
                f.write('\r\n')                
                
                
    def zap_save_active_session(self, session_name, target):
        """

        Writes out the current session zips it up and saves it to the target.
           session_name is full path to where we want to temporally export the session.
           target is were we want the gzip file to go.

        Examples:

        | zap save active session  | session_name  |  target |

        """
        
        results = self.zap.core.save_session(session_name)
        filelist = glob.glob("{}*".format(session_name))
        
        with tarfile.open(target, mode="w:gz") as f:
            for i in filelist:
                f.add(i)
                         
    
    def zap_write_to_json_file(self, target):
        """

        Fetches all the results from zap.core.alerts() and writes to json file.

        Examples:

        | zap write to json  | target |

        """
        core = self.zap.core
        all_vuls = []
        for i, na in enumerate(core.alerts(baseurl=target)):
            vul = {}
            vul["name"] = na["alert"]
            vul["confidence"] = na.get("confidence", "")
            vul["risk_text"] = na.get("risk")
            if na.get("risk") == "High":
                vul["severity"] = 3
            elif na.get("risk") == "Medium":
                vul["severity"] = 2
            elif na.get("risk") == "Low":
                vul["severity"] = 1
            else:
                vul["severity"] = 0

            vul["cwe"] = na.get("cweid", 0)
            vul["uri"] = na.get("url", "")
            vul["param"] = na.get("param", "")
            vul["attack"] = na.get("attack", "")
            vul["evidence"] = na.get("evidence", "")
            vul["pluginId"] = na.get("pluginId", "")
            message_id = na.get("messageId", "")
            message = core.message(message_id)
            if message:
                vul["requestHeader"] = message["requestHeader"]
                vul["responseHeader"] = message["responseHeader"]
                vul["rtt"] = int(message["rtt"])
            all_vuls.append(vul)

        filename = "{0}.json".format(str(uuid.uuid4()))
        with open(filename, "w") as json_file:
            json.dump(all_vuls, json_file, indent=2, separators=(',', ':'))

        return filename

    def zap_write_to_orchy(self, report_file, secret, access, hook_uri):
        """
                Generates an XML Report and writes said report to orchestron over a webhook.

                Mandatory Fields:
                - Report_file: Absolute Path of Report File - JSON or XML
                - Token: Webhook Token
                - hook_uri: the unique URI to post the XML Report to

                Examples:

                | zap write to orchy  | report_file_path | token | hook_uri

        """
        # xml_report = self.zap.core.xmlreport()
        # with open('zap_scan.xml','w') as zaprep:
        #     zaprep.write(xml_report)
        try:
            files = {"file": open(report_file, "rb")}
            auth = {"Secret-Key": secret, "Access-Key": access}
            r = requests.post(hook_uri, headers=auth, files=files)
            if r.status_code == 200:
                return "Successfully posted to Orchestron"
            else:
                raise Exception("Unable to post successfully")
        except Exception as e:
            print(e)

    def zap_write_html_report(
        self, export_dir, report_name
    ):
        """
        use the build in ZAP html Reporter
        """
        write_report( os.path.join(export_dir, report_name), self.zap.core.htmlreport())
        
    def zap_write_json_report(
        self, export_dir, report_name
    ):
        """
        use the build in ZAP json Reporter
        """
        write_report( os.path.join(export_dir, report_name), self.zap.core.jsonreport())

    def zap_write_md_report(
        self, export_dir, report_name
    ):
        """
        use the build in ZAP markdown Reporter
        """
        write_report( os.path.join(export_dir, report_name), self.zap.core.mdreport())
    
    def zap_write_xml_report(
        self, export_dir, report_name
    ):
        """
        use the build in ZAP markdown Reporter
        """
        write_report( os.path.join(export_dir, report_name), self.zap.core.xmlreport())    
    
    def zap_get_report_defaults(self, target):
        """
        Returns a default dictionary for exporting a report.  To be used to send
            into zap export report
            
            This can be used to turn on and off different aspects of the reports
            for alert severity t and f are used to turn on (t) or off (f) a specific
            function of the report.  See: https://www.zaproxy.org/docs/desktop/addons/export-report/
            NOTE: Alert Severity is backwards in the documentation.
            
            alert_severity - 'f;t;t;t'  
                Informational
                Low
                Medium
                High
                
            alert_details - "t;t;t;t;t;t;t;t;f;f"
               cwe id
               wasc id
               description
               other info
               solution
               reference
               request header
               response header
               request body
               response body
               
               
        Examples:
        
        | zap get report defaults  |  target  |
        
        """
        
        report_defaults = {
            'title': 'Vulnerability Report - {}'.format(target),
            'extension': 'xhtml',
            'description': 'Vulnerability report for the urls reference in scan of {}'.format(target),
            'prepared_by': 'Zap Scanner',
            'prepared_for': 'company',
            'scan_date': datetime.now().strftime("%I:%M%p on %B %d, %Y"),
            'report_date': datetime.now().strftime("%I:%M%p on %B %d, %Y"),
            'scan_version': "N/A",
            'report_version': "N/A",
            'alert_severity': "t;t;t;t",
            'alert_details': "t;t;t;t;t;t;t;t;f;f"}
            
        return report_defaults    
 
    
    def zap_export_report(self, export_file, report_settings):
        """
        This functionality works on ZAP > 2.7.0 with the export report plugin installed. 
        It leverages the Export Report Library to generate a report.
        Currently ExportReport doesnt have an API endpoint in python. We will be using the default ZAP REST API for this.
        See zap_get_report_defaults for documentation on report_settings.

        Examples:

        | zap export report | export_file | report_settings |

        """

        url = "http://localhost:{0}/JSON/exportreport/action/generate/".format(
            self.port
        )
        export_path = "{}.{}".format(export_file, report_settings['extension'])
        source_info = "{title};{prepared_by};{prepared_for};{scan_date};{report_date};{scan_version};{report_version};{description}".format(**report_settings)
        print("Alert Severity: {}".format(report_settings['alert_severity']))
        data = {
            "absolutePath": export_path,
            "fileExtension": report_settings['extension'],
            "sourceDetails": source_info,
            "alertSeverity": report_settings['alert_severity'],
            "alertDetails": report_settings['alert_details'],
        }

        r = requests.post(url, data=data)
        if r.status_code == 200:
            pass
        else:
            raise Exception("Unable to generate report")

    def zap_load_script(
        self,
        script_name,
        script_type,
        script_engine,
        script_file,
        desc="Generic Description of a ZAP Script",
    ):
        """        
        :param script_name:
        :param script_type:
        :param script_engine:
        :param script_file:
        :param desc:
        :return:
        """
        zap_script_status = self.zap.script.load(
            scriptname=script_name,
            scripttype=script_type,
            scriptengine=script_engine,
            filename=script_file,
            scriptdescription=desc,
        )
        logger.info(zap_script_status)

    def zap_run_standalone_script(self, script_name):
        zap_script_run_status = self.zap.script.run_stand_alone_script(script_name)
        logger.info(zap_script_run_status)

    def zap_shutdown(self):
        """
        Shutdown process for ZAP Scanner
        """
        self.zap.core.shutdown()
        time.sleep(5)
        fileList = glob.glob("{}*".format(self.session), recursive=True)
        for filePath in fileList:
            try:
                os.remove(filePath)
            except:
                time.sleep(1)
                print("Could not delete {}".format(filePath))
        
        #Reset the tempfile incase this gets resued
        temp_name = str(uuid.uuid4())
        tmp_dir = os.getcwd()
        self.session = os.path.join(tmp_dir, temp_name)
