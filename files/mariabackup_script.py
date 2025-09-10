#!/usr/bin/python3
from subprocess import Popen, PIPE, CalledProcessError
from subprocess import run as cmd_run
from argparse import ArgumentParser
from shutil import rmtree
from time import strftime, mktime, sleep
from datetime import datetime, timedelta
import os


MARIADB_BACKUP_BINARY = '/usr/bin/mariadb-backup'
LOCK_FILE = '/var/run/mariabackup-galera/db_backup.pid'

def get_opts():
    parser = ArgumentParser(
        usage="python3 mariabackup_script <destdir> [--full-backup][--increment] [--suffix=<suffix>] [--defaults-file=<defaults-file>]",
        prog="Mariadb Backup Script",
        description="""
        This program makes a mariadb backup with Mariabackup
        """,
    )
    parser.add_argument(
        "destdir",
        help="Specifying directory for storing backups",
    )
    parser.add_argument(
        "-f",
        "--full-backup",
        action="store_true",
        dest="fullbackup_flag",
        default=False,
        help="Flag for creation of full backup",
    )
    parser.add_argument(
        "-i",
        "--increment",
        action="store_true",
        dest="increment_flag",
        default=False,
        help="Flag to make incremental backup, based on the latest backup",
    )
    parser.add_argument(
        "--compress",
        dest="compress_flag",
        default=False,
        type=eval,
        choices=[True, False],
        help="Flag to compress created backups",
    )
    parser.add_argument(
        "--compressor",
        dest="compressor",
        default="gzip",
        type=str,
        help="The compressor to use when compressing backups (default: gzip)",
    )
    parser.add_argument(
        "-c",
        "--copies",
        dest="copies_flag",
        default=False,
        type=int,
        help="Specifying how much copies to rotate",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        dest="check_flag",
        default=False,
        help="Checking last mariadb full backup for their relevancy",
    )
    parser.add_argument(
        "--warning",
        dest="warning_value",
        default=False,
        type=int,
        help="When to raise warning (for --check) in days",
    )
    parser.add_argument(
        "--critical",
        dest="critical_value",
        default=False,
        type=int,
        help="When to raise critical (for --check) in days",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        dest="suffix",
        default=False,
        type=str,
        help="Added to the filename of backups"
    )
    parser.add_argument(
        "--defaults-file",
        dest="defaults_file",
        type=str,
        help="A cnf file can specified to the mariabackup process"
    )
    opts = parser.parse_args()
    return opts


def check_backups(dest, warning, critical, full_backup_filename):
    try:
        full_backup_list = [
            os.path.normpath(dest+'/'+f)
            for f in os.listdir(dest)
            if f.startswith(full_backup_filename)
        ]
        last_mariabackup_full_name = max(full_backup_list, key=os.path.getmtime)
        last_mariabackup_full = datetime.strptime(
            last_mariabackup_full_name.split(full_backup_filename)[1], '%Y%m%d-%H%M%S'
        )
    except ValueError:
        print("No files found, you may need to check your destination directory or add a suffix.")
        raise SystemExit()

    warning_time = datetime.today() - timedelta(days=warning)
    critical_time = datetime.today() - timedelta(days=critical)
    print_info = "Last mariadb backup date "+str(last_mariabackup_full)

    if last_mariabackup_full < critical_time:
        print(print_info)
        raise SystemExit(2)
    elif last_mariabackup_full < warning_time:
        print(print_info)
        raise SystemExit(1)
    else:
        print(print_info)
        raise SystemExit(0)


def create_full_backup(dest, curtime, full_backup_filename, extra_mariabackup_args, compress, compressor):
    check_lock_file()
    get_lock_file()
    try:
        err = open(os.path.normpath(dest+"/backup.log"), "w")
        full_backup_base_path = os.path.normpath(f"{dest}/{full_backup_filename}{curtime}")
        if compress:
            # Creating compressed full backup
            os.makedirs(full_backup_base_path, exist_ok=True)
            mariabackup_default_args = [
                '--backup',
                '--stream=xbstream',
                '--extra-lsndir',
                full_backup_base_path,
            ]
            mariadb_backup_args = [MARIADB_BACKUP_BINARY] + extra_mariabackup_args+ mariabackup_default_args
            mariabackup_run = Popen(mariadb_backup_args, stdout=PIPE, stderr=err)

            compressed_backup_path = f"{full_backup_base_path}/{full_backup_filename}{curtime}"
            with open(os.path.normpath(compressed_backup_path), "wb") as compressed_backup:
                cmd_run([compressor], stdin=mariabackup_run.stdout, stdout=compressed_backup)
                mariabackup_run.wait()
                mariabackup_res = mariabackup_run.communicate()
                if mariabackup_run.returncode:
                    print(mariabackup_res[1])
        else:
            # Creating full backup
            mariabackup_default_args = [
                '--backup',
                '--target-dir',
                full_backup_base_path
            ]

            cmd_run(
                [MARIADB_BACKUP_BINARY] + extra_mariabackup_args + mariabackup_default_args,
                text=True, check=True,
                stderr=err, stdout=None
            )

            #Preparing full backup
            mariabackup_default_prep_args = [
                '--prepare',
                '--target-dir',
                full_backup_base_path
            ]

            with open(os.path.normpath(dest+"/prepare.log"), "w") as err_p:
                cmd_run(
                    [MARIADB_BACKUP_BINARY] + extra_mariabackup_args + mariabackup_default_prep_args,
                    text=True, check=True,
                    stdout=None, stderr=err_p
                )

    except OSError:
        print("Please, check that Mariabackup is installed")
    except CalledProcessError as e:
        print(f"Failure exit code: {e.returncode}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(e)
    finally:
        os.unlink(LOCK_FILE)
        err.close()


def create_increment_backup(dest, curtime, increment_backup_filename, extra_mariabackup_args, compress, compressor):
    check_lock_file()
    get_lock_file()
    try:
        basedir = max(
            [
                os.path.normpath(dest+'/'+f)
                for f in os.listdir(dest)
                if f.startswith('mariabackup-')
            ], key=os.path.getmtime
        )
    except ValueError:
        print("No full backup found, cannot create incremental backup.")
        os.unlink(LOCK_FILE)
        raise SystemExit(1)
    try:
        err = open(os.path.normpath(dest+"/increment.err"), "w")
        increment_backup_base_path = os.path.normpath(f"{dest}/{increment_backup_filename}{curtime}")
        if compress:
            # Creating compressed incremental backup
            os.makedirs(increment_backup_base_path, exist_ok=True)
            mariabackup_default_args = [
                '--backup',
                '--stream=xbstream',
                '--incremental-basedir', basedir,
                '--extra-lsndir', increment_backup_base_path
            ]
            mariadb_backup_args = [MARIADB_BACKUP_BINARY] + extra_mariabackup_args + mariabackup_default_args
            mariabackup_run = Popen(mariadb_backup_args, stdout=PIPE, stderr=err)
            compressed_backup_path = f"{increment_backup_base_path}/{increment_backup_filename}{curtime}"
            with open(os.path.normpath(compressed_backup_path), "wb") as compressed_backup:
                cmd_run([compressor], stdin=mariabackup_run.stdout, stdout=compressed_backup)
                mariabackup_run.wait()
                mariabackup_res = mariabackup_run.communicate()
                if mariabackup_run.returncode:
                    print(mariabackup_res[1])
        else:
            # Creating incremental backup
            mariabackup_default_args = [
                '--backup',
                '--target-dir', increment_backup_base_path,
                '--incremental-basedir', basedir
            ]
            cmd_run(
                [MARIADB_BACKUP_BINARY] + extra_mariabackup_args + mariabackup_default_args,
                text=True, check=True,
                stderr=err, stdout=None
            )

    except OSError:
        print("Please, check that Mariabackup is installed")
    except CalledProcessError as e:
        print(f"Failure exit code: {e.returncode}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(e)
    finally:
        os.unlink(LOCK_FILE)
        err.close()


def rotate_backups(dest, copies, full_backup_filename, increment_backup_filename):
    check_lock_file()
    get_lock_file()
    full_list = [os.path.normpath(dest+'/'+f) for f in os.listdir(dest) if f.startswith(full_backup_filename)]
    increment_list = [ os.path.normpath(dest+'/'+f) for f in os.listdir(dest) if f.startswith(increment_backup_filename)]
    # Rotate full backups
    if len(full_list) > copies:
        full_list.sort()
        while len(full_list) > copies:
            oldest_full_backup = min(full_list, key=os.path.getmtime)
            full_list.remove(oldest_full_backup)
            rmtree(oldest_full_backup)
        # Remove all incremental backups older than the oldest full backup
        oldest_full_backup_timestamp = parsedate(oldest_full_backup.split(full_backup_filename)[1])
        for increment in increment_list:
            increment_timestamp = parsedate(increment.split(increment_backup_filename)[1])
            if increment_timestamp < oldest_full_backup_timestamp:
                rmtree(increment)
    os.unlink(LOCK_FILE)


def parsedate(s):
    return mktime(datetime.strptime(s, '%Y%m%d-%H%M%S').timetuple())


def check_lock_file():
    timer = 0
    while os.path.isfile(LOCK_FILE):
        sleep(60)
        timer += 1
        if timer == 120:
            print("timeout of waiting another process is reached")
            raise SystemExit(1)


def get_lock_file():
    try:
        with open(LOCK_FILE, 'w') as pid:
            pid.write(str(os.getpid()))
    except Exception as e:
        print(e)


def main():
    opts = get_opts()
    curtime = strftime("%Y%m%d-%H%M%S")

    if not opts.copies_flag and opts.fullbackup_flag:
        raise NameError("--copies flag is required for running full backup.")

    full_backup_filename = "mariabackup-full_"
    increment_backup_filename = "mariabackup-increment_"
    if opts.suffix:
        full_backup_filename = ("mariabackup-full-" + opts.suffix + "_")
        increment_backup_filename = ("mariabackup-increment-" + opts.suffix + "_")

    extra_mariabackup_args = []
    # --defaults-file must be specified straight after the process
    if opts.defaults_file:
        extra_mariabackup_args.append("--defaults-file=" + opts.defaults_file)

    if opts.fullbackup_flag and opts.increment_flag:
        raise NameError("Only one flag can be specified per operation")
    elif opts.fullbackup_flag:
        create_full_backup(opts.destdir, curtime, full_backup_filename, extra_mariabackup_args, opts.compress_flag, opts.compressor)
        rotate_backups(opts.destdir, opts.copies_flag, full_backup_filename, increment_backup_filename)
        raise SystemExit()
    elif opts.increment_flag:
        create_increment_backup(opts.destdir, curtime, increment_backup_filename, extra_mariabackup_args, opts.compress_flag, opts.compressor)
        raise SystemExit()
    elif opts.check_flag:
        pass
    else:
        raise NameError("either --increment or --full-backup flag is required")

    if opts.check_flag and (opts.warning_value and opts.critical_value):
        check_backups(
            warning=opts.warning_value,
            critical=opts.critical_value,
            dest=opts.destdir,
            full_backup_filename=full_backup_filename
        )
    else:
        raise NameError("--warning and --critical thresholds should be specified for check")


if __name__ == "__main__":
    main()
