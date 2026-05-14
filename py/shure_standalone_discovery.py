import json
from optparse import OptionParser
import os
import platform
import sys
import xml.etree.ElementTree as ET

from shure.discover import ShureDiscovery


class StandaloneShureDiscovery:

    DCID_XML_FILENAME = 'DCIDMap.xml'
    DEFAULT_DCID_XML = {
        "Darwin": '/Applications/Shure Update Utility.app/Contents/Resources',
        "Windows": 'C:\\Program Files\\Shure\\Shure Update Utility'
    }

    def __init__(self):
        self.discovery = None
        
    def process_discovery_packet(self, ip, data):
        # Get DCID of device
        dcid = self.discovery.get_dcid_from_slp_attrs(*self.discovery.get_attrs_from_slp(data))
        
        # Get device definition matching DCID
        device = self.discovery.get_dcid_definition(dcid)

        print(f"Found a {device['model_name']} at {ip}")

    def DCIDMapCheck(self):
        system = platform.system()
        if system not in self.DEFAULT_DCID_XML:
            return None
        path = os.path.join(self.DEFAULT_DCID_XML[system], self.DCID_XML_FILENAME)
        if os.path.isfile(path):
            return path
        return None

    def DCID_Parse(self, file):
        tree = ET.parse(file)
        root = tree.getroot()

        devices = root.findall('./MapEntry')
        device_list = {}

        for device in devices:
            if device.find("PkgType").text != "Primary":
                continue
            model = device.find('Key').text
            model_name = device.find('ModelName').text
            dcid = []
            for dccid in device.find('DCIDList').iter('DCID'):
                band = dccid.attrib['band'] if 'band' in dccid.attrib else ''
                device_list[dccid.text] = {
                    'model': model,
                    'model_name': model_name,
                    'band': band,
                }
        return device_list

    def dcid_save_to_file(self, filepath, contents):
        with open(filepath, 'w') as f:
            json.dump(contents, f, indent=2, separators=(',', ': '), sort_keys=True)
            f.write('\n')

    def updateDCIDmap(self, inputFile, outputFile):
        contents = self.DCID_Parse(inputFile)
        self.dcid_save_to_file(outputFile, contents)

    def main(self):
        usage = "usage: %prog [options] arg"
        parser = OptionParser(usage)

        parser.add_option("-i", "--input", dest="input_file",
                          help="DCID input file")
        parser.add_option("-o", "--output", dest="output_file",
                          help="output file")
        parser.add_option("-c", "--convert", default=False,
                          action="store_true", dest="convert",
                          help="Generate dcid.json from input DCIDMap.xml file")
        parser.add_option("-d", "--discover", default=True,
                          action="store_true", dest="discover",
                          help="Discover Shure devices on the network")

        (options, args) = parser.parse_args()

        if options.convert:
            if not options.output_file:
                print("use -o to specify a DCID output file destination")
                sys.exit()

            if options.input_file:
                p = options.input_file

            elif self.DCIDMapCheck():
                p = self.DCIDMapCheck()

            else:
                print("Specify an input DCIDMap.xml file with -i or install Wireless Workbench")
                sys.exit()

            if p:
                self.updateDCIDmap(p, options.output_file)
                print("Converting {} to {}".format(p, options.output_file))
            sys.exit()

        if options.discover:
            print("lets discover some stuff")
            self.discovery = ShureDiscovery(self.process_discovery_packet)
            self.discovery.start()


if __name__ == '__main__':
    app = StandaloneShureDiscovery()
    app.main()

