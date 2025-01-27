from hacmony.hacmony import HACMony
from hacmony.device import Device 
from hacmony.app import App
from hacmony.hstg import HSTG
import argparse
from loguru import logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', help='sub-command help')
    parser_devices = subparsers.add_parser('devices', help='list connected devices')
    parser_explore = subparsers.add_parser('explore', help='explore the app')
    parser_detect = subparsers.add_parser('detect', help='detect bugs')

    parser_explore.add_argument('app_path', type=str, help='specify the app path for exploration')
    parser_explore.add_argument('-s', '--serial', type=str, help='specify the device serial for exploration')
    parser_explore.add_argument('-d', '--depth', type=int, default=2, help='specify the depth of exploration, default is 2')
    parser_explore.add_argument('-o', '--output', type=str, default='output.xml', help='specify the output file path of hstg')
    parser_explore.add_argument('-t', '--timeout', type=int, default=30, help='specify the timeout of exploration')

    parser_detect.add_argument('--source_device', type=str, help='specify the source device serial for detection')
    parser_detect.add_argument('--target_device', type=str, help='specify the target device serial for detection')
    parser_detect.add_argument('--source_app', type=str, help='specify the source app path for detection')
    parser_detect.add_argument('--target_app', type=str, help='specify the target app path for detection')
    parser_detect.add_argument('--source_hstg', type=str, help='specify the source hstg path for detection')
    parser_detect.add_argument('--target_hstg', type=str, help='specify the target hstg path for detection')
    parser_detect.add_argument('-o', '--output', type=str, default='output.xml', help='specify the output file path of detection')
    args = parser.parse_args()
    if args.command == 'devices':
        from hacmony.utils import get_available_devices
        print(get_available_devices())
    if args.command == 'explore':
        serial = ''
        if args.serial:
            serial = args.serial
        else:
            from hacmony.utils import get_available_devices
            devices = get_available_devices()
            if len(devices) > 0:
                serial = devices[0]
            else:
                logger.warning("No device connected!")
                exit(0)
        depth = args.depth
        timeout = args.timeout
        hacmony = HACMony()
        device = Device(serial)
        hstg = hacmony.explore(device, depth, args.app_path, timeout)
        hstg.export_xml(args.output)

    if args.command == 'detect':
        source_device_serial = ''
        target_device_serial = ''
        if args.source_device:
            source_device_serial = args.source_device
        else:
            from hacmony.utils import get_available_devices
            devices = get_available_devices()
            if len(devices) > 1:
                serial = devices[0]
            else:
                logger.warning("No device connected!")
                exit(0)
        if args.target_device:
            target_device_serial = args.target_device
        else:
            from hacmony.utils import get_available_devices
            devices = get_available_devices()
            if len(devices) > 1:
                serial = devices[1]
            else:
                logger.warning("No device connected!")
                exit(0)
        
        source_app_path = ''
        target_app_path = ''
        if args.source_app:
            source_app_path = args.source_app
        else:
            logger.warning("No source app path!")
        if args.target_app:
            target_app_path = args.target_app
        else:
            logger.warning("No target app path!")
        source_hstg_path = ''
        target_hstg_path = ''
        if args.source_hstg:
            source_hstg_path = args.source_hstg
        else:
            logger.warning("No source hstg path!")
        if args.target_hstg:
            target_hstg_path = args.target_hstg
        else:
            logger.warning("No target hstg path!")
        source_device = Device(source_device_serial)
        target_device = Device(target_device_serial)
        source_app = App(source_device, source_app_path)
        target_app = App(target_device, target_app_path)
        source_hstg = HSTG(source_device)
        target_hstg = HSTG(target_device)
        source_hstg.import_xml(source_hstg_path)
        target_hstg.import_xml(target_hstg_path)
        hacmony = HACMony()
        statuses = hacmony.detect_hac(source_device, source_app, source_hstg, target_device, target_app, target_hstg)

