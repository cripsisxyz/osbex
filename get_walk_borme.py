import requests, xmltodict, json, bormeparser, os

def download_raw_xml(borme_id):
    raw_xml = requests.get(f'https://www.boe.es/diario_borme/xml.php?id={borme_id}')
    return raw_xml

def xml_to_jstring(raw_xml):
    borme_dict = xmltodict.parse(raw_xml.text)
    borme_xml_json = json.dumps(borme_dict, ensure_ascii=False).encode('utf8')
    borme_xml_jstring = borme_xml_json.decode()
    return borme_xml_jstring

def download_parse_pdf(pdf_url):
    raw_pdf = requests.get(f'https://www.boe.es{pdf_url}', allow_redirects=True)
    pdf_path = f"/tmp/{pdf_url.split('/')[-1]}"
    open(pdf_path, 'wb').write(raw_pdf.content)

    bormeparser.parse(pdf_path, bormeparser.SECCION.A).to_json(f"{pdf_path}.json")
    
    with open(f"{pdf_path}.json") as f:
        data = json.load(f)
    os.remove(f"{pdf_path}.json")
    os.remove(pdf_path)
    
    return data

def get_borme_info(borme_jstring, requested_zone):
    borme_dict = json.loads(borme_jstring)

    needed_data = {}
    needed_data['metadata'] = {}
    needed_data['A'] = []
    #needed_data['B'] = {}

    a_section_idx = None
    b_section_idx = None
    c_section_idx = None
    if "error" in borme_dict.keys():
        return {'metadata': {'zone': requested_zone}, 'error': borme_dict}
    else:
        needed_data['metadata']['pub_date'] = borme_dict['sumario']['meta']['fecha']
        needed_data['metadata']['zone'] = requested_zone
        needed_data['metadata']['next_pub_date'] = borme_dict['sumario']['meta']['fechaSig']
    for section in borme_dict['sumario']['diario']['seccion']:
        if section['@num'] == "A":
            a_section_idx = borme_dict['sumario']['diario']['seccion'].index(section)
        if section['@num'] == "B":
            b_section_idx = borme_dict['sumario']['diario']['seccion'].index(section)
        if section['@num'] == "C":
            c_section_idx = borme_dict['sumario']['diario']['seccion'].index(section)

    # A
    for zoneinfo in borme_dict['sumario']['diario']['seccion'][a_section_idx]['emisor']['item']:
        if zoneinfo['titulo'] == requested_zone:
            needed_data['A'].append({
                'category': borme_dict['sumario']['diario']['seccion'][a_section_idx]['@nombre'],
                'subcategory': borme_dict['sumario']['diario']['seccion'][a_section_idx]['emisor']['@nombre'],
                'pdf_url': zoneinfo['urlPdf']['#text'],
                'pdf_raw_data': download_parse_pdf(zoneinfo['urlPdf']['#text'])
            })
    #B
    if needed_data['A']:
        return needed_data
    else:
        return {}

if __name__ == "__main__":
    
    requested_zones = ["A CORUÑA", "PONTEVEDRA"]
    #requested_zones = ["A CORUÑA"]

    for requested_zone in requested_zones:
        requested_date = "2021-03-10"
        rdate = requested_date.split("-")
        borme_xml_id = f"BORME-S-{rdate[0]}{rdate[1]}{rdate[2]}"
        completed_cycle = False

        while not completed_cycle:
            print("INTEEEEEEERACIOOOOOOOON")

            borme_jstring = xml_to_jstring(download_raw_xml(borme_xml_id))
            borme_data = get_borme_info(borme_jstring, requested_zone)
            
            if borme_data:
                if borme_data['metadata']['next_pub_date']:
                    rdate = borme_data['metadata']['next_pub_date'].split('/')
                    borme_old_id = borme_xml_id
                    borme_xml_id = f"BORME-S-{rdate[2]}{rdate[1]}{rdate[0]}"

                    print(json.dumps(get_borme_info(borme_jstring, requested_zone)))

                    if borme_old_id == borme_xml_id:
                        completed_cycle = True
                else:
                    print(json.dumps(get_borme_info(borme_jstring, requested_zone)))
                    completed_cycle = True

                