
from tapipy.actors import get_context


def archive_to_system(tapis_client, system_id, path, project_id, archive_type):
    file_list = []
    project = tapis_client.streams.get_project(project_uuid = project_id)
    sites = tapis_client.streams.list_sites(project_uuid = project_id)
    #print(sites)
    for site in sites:
        instruments = site.instruments
        for instrument in instruments:
            result = tapis_client.streams.list_measurements(inst_id=instrument_id,
                                                        project_uuid=project_id,
                                                        site_id=site_id,
                                                        start_date='2021-01-01T00:00:00Z',
                                                        end_date='2025-12-30T22:19:25Z',
                                                        format='csv')
            filename = instrument.inst_name+'.csv'
            with open(filename, 'wb') as f:
                f.write(result)
            f.close()
            file_list.append(filename)
    if (archive_type == "zip"):
        #create zip archive
        print("zip")
    else:
      #create tar
    #upload file to system at the path
    tapis_client.upload(source_file_path="zipfile", system_id=system_id, dest_file_path=path)

context = get_context()
message = context['raw_message']
archive_to_system(message['system_id'], message['path'], message['project_id'], message['archive_type'])
