import os,sys
import sqlite3
import glob
import shutil

if __name__=='__main__':

    db_file = sys.argv[1]
    out_path = sys.argv[2]

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    for row in c.execute("SELECT CrystalName, "
                         "DataProcessingPathToLogfile "
                         "FROM mainTable "
                         "WHERE RefinementOutcome='6 - Deposited'"):
        xtal = row[0]
        aimless_path = row[1]
        aimless_log = glob.glob(os.path.join(aimless_path,"*aimless*"))[0]
        aimless_out = os.path.join(out_path, xtal, "aimelss.log" )
        shutil.copy(aimless_log, aimless_out)