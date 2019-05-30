
import requests
from bs4 import BeautifulSoup
from time import strftime
import re
import os


def main():
    """
    Retrieves an updated list of photometric systems defined in the CMD
    service.
    Store final data in 'phot_systs_NEW.dat' file, and compare with the 'OLD'
    version stored.

    Also generates the 'CMD_systs.dat' file that ASteCa uses.
    """
    # Actual date/time
    now_time = strftime("%Y-%m-%d %H:%M:%S")
    # Download data.
    version, systs = downlData()

    syst_ids, syst_names = systemsClean(systs)

    # Create data file with effective lambdas and omegas for each filter, for
    # each photometric system defined.
    flo = []  # filters, lambdas, omegas
    for syst in syst_ids:
        data = outPage(syst)
        if data is not None:
            flo.append(data)

    CMDsystsFile(now_time, version, syst_ids, flo)

    # Create properly formatted file.
    photSystsFile(now_time, version, syst_ids, syst_names, flo)
    # # Check for changes.
    versionsCompare()


def downlData():
    """
    Download necessary data from the CMD live version.
    """
    r = requests.get('http://stev.oapd.inaf.it/cgi-bin/cmd')
    soup = BeautifulSoup(r.content, "lxml")
    version = soup.find_all("center")[0]
    systs = soup.find_all("select")[0]

    return version, systs


def systemsClean(systs):
    """
    """
    replc = ["""<option value="tab_mag_odfnew/tab_mag_""",
             """<option selected="" value="tab_mag_odfnew/tab_mag_""",
             "</option>", "<i>", "</i>", "<sub>", "</sub>"]

    syst_ids, syst_names = [], []
    for s in systs:
        sr = str(s)
        for _ in replc:
            sr = sr.replace(_, "")
        sr = [_.strip() for _ in sr.split(""".dat">""")]
        if sr[0] != "":
            syst_ids.append(sr[0])
            syst_names.append(sr[1])

    return syst_ids, syst_names


def outPage(phot_syst):
    """
    Get lambda-omega data.
    """
    d = {
        "submit_form": (None, "Submit"),
        "cmd_version": (None, "3.2"),
        "track_postagb": (None, "no"),
        "n_inTPC": (None, "10"),
        "eta_reimers": (None, "0.2"),
        "kind_interp": (None, "1"),
        "kind_postagb": (None, "-1"),
        "photsys_version": (None, "YBC"),
        "dust_sourceM": (None, "dpmod60alox40"),
        "dust_sourceC": (None, "AMCSIC15"),
        "kind_mag": (None, "2"),
        "kind_dust": (None, "0"),
        "extinction_av": (None, "0.0"),
        "extinction_coeff": (None, "constant"),
        "extinction_curve": (None, "cardelli"),
        "isoc_isagelog": (None, "1"),
        "isoc_ismetlog": (None, "0"),
        "isoc_zupp": (None, "0.03"),
        "isoc_dz": (None, "0.0"),
        "output_kind": (None, "0"),
        "output_evstage": (None, "1"),
        "lf_maginf": (None, "-15"),
        "lf_magsup": (None, "20"),
        "lf_deltamag": (None, "0.5"),
        "sim_mtot": (None, "1.0e4"),
        "track_parsec": (None, "parsec_CAF09_v1.2S"),
        "track_colibri": (None, "parsec_CAF09_v1.2S_S35"),
        'isoc_zlow': (None, "0.0152"),
        'isoc_lagelow': (None, "6.6"),
        'isoc_lageupp': (None, "10.13"),
        'isoc_dlage': (None, "0.0"),
        'imf_file': (None, "tab_imf/imf_kroupa_orig.dat")}

    d['photsys_file'] = (
        None, 'tab_mag_odfnew/tab_mag_{0}.dat'.format(phot_syst))

    print("  Fetching '{}'".format(phot_syst))

    # TODO remove when 'decam_vista' system supports 'YBC'
    if phot_syst == 'decam_vista':
        d['photsys_version'] = (None, "odfnew")
    else:
        d['photsys_version'] = (None, "YBC")

    webserver = 'http://stev.oapd.inaf.it'
    c = requests.post(webserver + '/cgi-bin/cmd', files=d).text

    try:
        # Extract filters, lambdas, and omegas data
        aa = re.compile('Filter.*<th>&lambda')
        fname = aa.findall(c)
        # In CMD v3.2 apparently all filters have a 'mag' added.
        filters = [
            _.split('</td>')[0] + 'mag' for _ in fname[0].split('<td>')][1:]
        aa = re.compile('lambda.*omega')
        fname = aa.findall(c)
        lambdas = [_.split('</td>')[0] for _ in fname[0].split('<td>')][1:]
        aa = re.compile('omega.*lambda')
        fname = aa.findall(c)
        omegas = [_.split('</td>')[0] for _ in fname[0].split('<td>')][1:]
    except Exception as err:
        # print(err)
        err_i = c.index("errorwarning")
        txt = c[err_i + 17:err_i + 17 + 100]
        print('\n' + txt.split("<br>")[0].replace("</b>", ""), '\n')
        return None

    return filters, lambdas, omegas


def CMDsystsFile(now_time, version, syst_ids, flo):
    """
    """
    with open("CMD_systs.dat", "w") as f:
        f.write("#\n# Photometric Systems, {}\n".format(
            version.string.replace(" input form", "")))
        f.write("#\n# Retrieved: {}\n#\n".format(now_time))
        f.write("#{:<3} {:<50} {}   {}   {}\n".format(
            "ID", "System ID", "Filters", "Lambdas", "Omegas"))
        for i, s in enumerate(flo):
            f.write("{:<3}  {:<50} {}   {}   {}\n".format(
                i, syst_ids[i], "  ".join(s[0]), "  ".join(s[1]),
                "  ".join(s[2])))


def photSystsFile(now_time, version, syst_ids, syst_names, flo):
    """
    Create the new (most recent) version of the photometric systems file.
    """

    with open("phot_systs_NEW.dat", "w") as f:
        f.write("#\n# Photometric Systems, {}\n".format(
            version.string.replace(" input form", "")))
        f.write("#\n# Retrieved: {}\n#\n".format(now_time))
        f.write("#{:<3} {:<40}{:<120}{}\n".format(
            "ID", "System ID", "Photometric system", "Filters"))
        for i, sid in enumerate(syst_ids):
            f.write("{:<3}  {:<40}{:<120}{}\n".format(
                i, sid, syst_names[i], "   ".join(flo[i][0])))

    return syst_names


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


if __name__ == '__main__':
    main()
