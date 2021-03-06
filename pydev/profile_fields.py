
# coding: utf-8
#!/usr/bin/env python

from optparse import OptionParser
from ConfigUtils import *
from SocrataStuff import *
from PandasUtils import *
from PyLogger import *
from ProfileFields import *
from Utils import *
from JobStatusEmailerComposer import *


def parse_opts():
  helpmsgConfigFile = 'Use the -c to add a config yaml file. EX: fieldConfig.yaml'
  parser = OptionParser(usage='usage: %prog [options] ')
  parser.add_option('-c', '--configfile',
                      action='store',
                      dest='configFn',
                      default=None,
                      help=helpmsgConfigFile ,)

  helpmsgConfigDir = 'Use the -d to add directory path for the config files. EX: /home/ubuntu/configs'
  parser.add_option('-d', '--configdir',
                      action='store',
                      dest='configDir',
                      default=None,
                      help=helpmsgConfigDir ,)
  helpmsgjobType = 'Use the -n to specify a job name. EX: profile_fields -EX: profile_fields - can either be profile_datasets or profile_fields'
  parser.add_option('-n', '--jobtype',
                      action='store',
                      dest='jobType',
                      default=None,
                      help=helpmsgjobType ,)

  (options, args) = parser.parse_args()

  if options.configFn is None:
    print "ERROR: You must specify a config yaml file!"
    print helpmsgConfigFile
    exit(1)
  elif options.configDir is None:
    print "ERROR: You must specify a directory path for the config files!"
    print helpmsgConfigDir
    exit(1)
  elif options.jobType is None:
    print "ERROR: You must specify a directory path for the config files!"
    print helpmsgjobType
    exit(1)

  config_inputdir = None
  fieldConfigFile = None
  fieldConfigFile = options.configFn
  config_inputdir = options.configDir
  jobType =  options.jobType
  return fieldConfigFile, config_inputdir, jobType


def main():
  fieldConfigFile, config_inputdir, jobType = parse_opts()
  cI =  ConfigUtils(config_inputdir,fieldConfigFile )
  configItems = cI.getConfigs()
  configItems['dataset_name'] =  jobType
  lg = pyLogger(configItems)
  logger = lg.setConfig()
  logger.info("****************JOB START******************")
  sc = SocrataClient(config_inputdir, configItems, logger)
  client = sc.connectToSocrata()
  clientItems = sc.connectToSocrataConfigItems()
  scrud = SocrataCRUD(client, clientItems, configItems, logger)
  sQobj = SocrataQueries(clientItems, configItems, logger)

  mmdd_fbf = configItems['dd']['master_dd']['fbf']
  field_profiles_fbf =  configItems['dd']['field_profiles']['fbf']
  base_url =  configItems['baseUrl']

  field_type_fbf =  configItems['dd']['field_type']['fbf']


  load_mm_dd = ProfileFields.getBaseDatasetJson(sQobj, configItems,  mmdd_fbf)
  #print load_mm_dd
  #load_mm_dd  = True
  current_field_profiles = ProfileFields.getCurrentFieldProfiles(sQobj, base_url, field_profiles_fbf)

  if load_mm_dd :
    master_dfList = ProfileFields.get_dataset_as_dfList(configItems['pickle_data_dir'], configItems['mm_dd_json_fn'], base_url)
    ProfileFields.removeDeletedFields(scrud,  field_profiles_fbf, master_dfList,  current_field_profiles)
    current_field_profiles = ProfileFields.getCurrentFieldProfiles(sQobj, base_url, field_profiles_fbf)

    dataset_info = ProfileFields.buildInsertFieldProfiles(sQobj, scrud, configItems, master_dfList, current_field_profiles)
    print dataset_info
    dsse = JobStatusEmailerComposer(configItems, logger, jobType)
    if dataset_info['DatasetRecordsCnt'] > 1:
      dsse.sendJobStatusEmail([dataset_info])
    else:
      dataset_info = {'Socrata Dataset Name': configItems['dataset_name'], 'SrcRecordsCnt':0, 'DatasetRecordsCnt':0, 'fourXFour': "Nothing to Insert"}
      dataset_info['isLoaded'] = 'success'
      dsse.sendJobStatusEmail([dataset_info])






if __name__ == "__main__":
    main()
