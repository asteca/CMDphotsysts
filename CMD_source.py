
import requests
from bs4 import BeautifulSoup
from time import strftime
import os


def downlData():
    """
    Download necessary data from the CMD live version.
    """
    r = requests.get('http://stev.oapd.inaf.it/cgi-bin/cmd')
    soup = BeautifulSoup(r.content, "lxml")
    version = soup.find_all("center")[0]
    systs = soup.find_all("select")[0]

    return version, systs


def frmtFile(now_time, version, systs):
    """
    Create the new (most recent) version of the photometric systems file.
    """
    replc = ["""<option value="tab_mag_odfnew/tab_mag_""",
             """<option selected="selected" value="tab_mag_odfnew/tab_mag_""",
             "</option>", "<i>", "</i>", "<sub>", "</sub>"]

    i = 0
    with open("phot_systs_NEW.dat", "w") as f:
        f.write("# Photometric Systems, {}\n".format(
            version.string.replace(" input form", "")))
        f.write("#\n# Retrieved: {}\n#\n".format(now_time))
        f.write("# {:<6}{:<40}{}\n#\n".format(
            "ID", "CMD_ID", "Photometric system"))
        for s in systs:
            sr = str(s)
            for _ in replc:
                sr = sr.replace(_, "")
            sr = [_.strip() for _ in sr.split(""".dat">""")]
            if sr[0] != "":
                f.write("{:<8}{:<40}{}\n".format(i, *sr))
                i += 1


def versionsCompare():
    """
    Check if new version is different from the old one.
    """
    # Check if 'OLD' version of the file exists.
    oldExst = os.path.isfile("phot_systs_OLD.dat")

    if oldExst:
        with open("phot_systs_NEW.dat", "r") as f:
            newFile = f.readlines()
        # Remove commented lines.
        newFile = [_ for _ in newFile if not _.startswith('#')]
        with open("phot_systs_OLD.dat", "r") as f:
            oldFile = f.readlines()
        oldFile = [_ for _ in oldFile if not _.startswith('#')]
        if newFile == oldFile:
            print("No changes in new version.")
        else:
            print("New version contains changes.")
    else:
        print("No 'OLD' file present.")
        os.rename("phot_systs_NEW.dat", "phot_systs_OLD.dat")


def main():
    """
    Retrieves an updated list of photometric systems defined in the CMD
    service.
    Store final data in 'phot_systs_NEW.dat' file, and compare with the 'OLD'
    version stored.
    """
    # Actual date/time
    now_time = strftime("%Y-%m-%d %H:%M:%S")
    # Download data.
    version, systs = downlData()
    # Create properly formatted file.
    frmtFile(now_time, version, systs)
    # Check for changes.
    versionsCompare()


if __name__ == '__main__':
    main()
