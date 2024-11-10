

import glob
import logging
import multiprocessing
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from cdo import Cdo

cdo = Cdo(tempdir="tmp", silent=False)

logging.basicConfig(
    level=logging.INFO,  # Set the minimum log level (INFO, DEBUG, etc.)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    stream=sys.stdout  # Output logs to stdout
)




@dataclass
class DataStore:
    data_root: str
    exp_name: str

    def get_fcst_dates(self):
        # glob dirs in data_root/exp_name and return their fcst dates
        dirs = glob.glob(f"{self.data_root}/{self.exp_name}/*")
        return sorted([d.split("/")[-1] for d in dirs])


def cdo_execute(input, output="", options=""):
    if output and Path(output).exists():
        logging.info(f"Output exists. Not Executing: cdo {options} {input} {output}")
        return output
    logging.info(f"Executing: cdo {options} {input} {output}")
    res = cdo.copy(input=input, options=options)
    logging.info(f"Done: cdo {options} {input} {res}")
    if output:
        create_parent_directory(output)
        shutil.move(res, output)
        logging.info(f"Moved  {res} -> {output}")
        res = output
    return res
    
def create_parent_directory(path: str): 
    Path(path).parent.mkdir(parents=True, exist_ok=True)

@dataclass
class ProcessPr:
    idata_store: DataStore
    data_cache: str
    fld: str = "pr"
    def get_input_file_path(self, fcstdate, mem, fld):
        return f"{self.idata_store.data_root}/{self.idata_store.exp_name}/{fcstdate}/mem{mem}/outputs/wrf2d_{fld}.nc"
    
    def get_output_file_path(self, fcstdate, ens, fld):
        return f"{self.data_cache}/{self.idata_store.exp_name}/{fcstdate}/monthly/{ens}/{fld}.nc"
    
     
    def mon_mean(self):
        options="-r"
        inputs = []
        outputs = []
        res = {}
        for date in self.idata_store.get_fcst_dates():
            res[date] = {}
            for mem in range(1, 26):
                inputs.append(self.get_input(date, mem))
                outputs.append(self.get_output(date, mem))
                
        # multiprocessing.set_start_method("fork", force=True)
        workers = min(os.cpu_count()-2, len(inputs))
        logging.info(f"Using {workers} workers")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(
                cdo_execute,
                inputs,
                outputs,
                [options] * len(inputs),
            )
            
    def ens_stat(self, opr):
        opr_safe = opr.replace(",", "")
        options="-r"
        inputs = []
        outputs = []
        for date in self.idata_store.get_fcst_dates():
            input=f"-ens{opr} [ "
            for mem in range(1, 26):
                input = input + self.get_output(date, mem) + " "
            input = input + " ] "
            inputs.append(input)
            outputs.append(self.get_output_file_path(date, f"ens{opr_safe}", "pr"))
                
        # multiprocessing.set_start_method("fork", force=True)
        workers = min(os.cpu_count()-2, len(inputs))
        logging.info(f"Using {workers} workers")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(
                cdo_execute,
                inputs,
                outputs,
                [options] * len(inputs),
            )
            
    def ymonmean(self, lead_months=range(1, 7), ensstats=["median", "mean"]):
        options="-r"
        inputs = []
        outputs = []
        for lead_month in lead_months:
            for ensstat in ensstats:
                input = "-ymonmean -mergetime [ "
                for date in self.idata_store.get_fcst_dates():
                    input = input + f" -seltimestep,{lead_month+1} " + self.get_output_file_path(date, f"ens{ensstat}", self.fld)
            
                input = input + " ] "
                inputs.append(input)
                output = f"{self.data_cache}/{self.idata_store.exp_name}/ymonmean/lead{lead_month}/ens{ensstat}/{self.fld}.nc"
                outputs.append(output)
                
        # multiprocessing.set_start_method("fork", force=True)
        workers = min(os.cpu_count()-2, len(inputs))
        logging.info(f"Using {workers} workers")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(
                cdo_execute,
                inputs,
                outputs,
                [options] * len(inputs),
            )

    def get_input(self, date, mem):
        infile1 = self.get_input_file_path(date, mem, "RAINNC")
        infile2 = self.get_input_file_path(date, mem, "RAINC")
        infile = f"-add {infile1} {infile2}"
        input=f" -setattribute,{self.fld}@units=mm/sec -chname,RAINNC,{self.fld} -monmean -divc,3600 -sub -seltimestep,2/-1 {infile} -seltimestep,1/-2 {infile}"
        return input
    def get_output(self, date, mem):
        return self.get_output_file_path(date, f"mem{mem}", self.fld)
    

    

if __name__ == "__main__":
    data_store = DataStore(data_root="/scratch/athippp/cylc-archive", exp_name="ap84SeasRF")
    pr = ProcessPr(idata_store=data_store, data_cache="data_cache")
    pr.mon_mean() 
    pr.ens_stat("mean")
    pr.ens_stat("median")
    pr.ymonmean()