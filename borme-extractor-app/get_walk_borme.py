import requests, xmltodict, json, bormeparser, os, yaml, time, logging, sys, datetime

#
# NEED COMPLETE REFACTOR WITH CLASSES
#
def set_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(funcName)s:%(lineno)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

def load_config():
    try:
        yaml_conf_path = f"{os.getcwd()}/config/borme-extractor/checker.yml"
        with open(yaml_conf_path, 'r') as file:
            yaml_conf = yaml.full_load(file)
    except:
        logging.error(f"Imposible cargar configuración! ({yaml_conf_path}) saliendo...")
        exit()
    else:
        logging.info(f"Configuración cargada exitosamente ({yaml_conf_path})")
        return yaml_conf

def write_config(new_config):
    try:
        yaml_conf_path = f"{os.getcwd()}/config/borme-extractor/checker.yml"
        with open(yaml_conf_path, 'w') as file:
            yaml.dump(new_config, file)
    except:
        logging.error(f"Imposible escribir nueva configuración! ({yaml_conf_path}) saliendo...")
        exit()
    else:
        logging.info(f"Nueva configuración escrita exitosamente ({yaml_conf_path})")

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

def post_to_logstash(borme_data, output_config):
    url = f"http://{output_config['server']}:{output_config['port']}"

    if "error" in borme_data:
        logging.info(f"Descartado por no contener info correcta")
    else:
        x = requests.post(url, data = borme_data)

def get_borme_info(borme_jstring, requested_zone, borme_id):
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

    if needed_data['A']:
        return needed_data
    else:
        return {}


if __name__ == "__main__":
    
    # Seteamos el formato del logger y que printee al stdout
    set_logger()

    # Entramos en bucle infinito para que el contenedor se mantenga siempre activo
    while True:

        logging.info(f"Incializando app")

        # Cargamos el YAML de configuración
        yaml_conf = load_config()

        # Recogemos las zonas necesarias del YAML
        requested_zones = []

        for key, value in yaml_conf['zones'].items():
            requested_zones.append(key)
        
        # Para cada zona..
        for requested_zone in requested_zones:

            completed_cycle = False

            while not completed_cycle:
                # Recargamos el YAML de configuración en busqueda 
                yaml_conf = load_config()
                requested_date = yaml_conf['zones'][requested_zone]['last_checked']

                logging.info(f"Inciando proceso para zona {requested_zone} para el día {requested_date}")

                rdate = requested_date.split("-")
                borme_xml_id = f"BORME-S-{rdate[0]}{rdate[1]}{rdate[2]}"
                
                logging.info(f"Descargando XML base del día..")
                borme_jstring = xml_to_jstring(download_raw_xml(borme_xml_id))

                logging.info(f"Descargando PDF del día para esta zona..")
                logging.info(f"Recopilando datos del boletín..")
                try:
                    borme_data = get_borme_info(borme_jstring, requested_zone, borme_xml_id)
                except:
                    pass
                
                if borme_data:
                    if "next_pub_date" in borme_data['metadata'] and borme_data['metadata']['next_pub_date'] is not None:

                        rdate = borme_data['metadata']['next_pub_date'].split('/')
                        borme_old_id = borme_xml_id
                        borme_xml_id = f"BORME-S-{rdate[2]}{rdate[1]}{rdate[0]}"
                        yaml_conf['zones'][requested_zone]['last_checked'] = f"{rdate[2]}-{rdate[1]}-{rdate[0]}"
                        write_config(yaml_conf)
                        #print(json.dumps(get_borme_info(borme_jstring, requested_zone)))

                        logging.info(f"Recopilando datos del boletín..")
                        try:
                            post_to_logstash(json.dumps(get_borme_info(borme_jstring, requested_zone, borme_xml_id)), yaml_conf["output_http"])
                        except:
                            pass

                        if borme_old_id == borme_xml_id:
                            completed_cycle = True
                    else:
                        
                        #borme_data

                        try:
                            post_to_logstash(json.dumps(get_borme_info(borme_jstring, requested_zone, borme_xml_id)), yaml_conf["output_http"])
                        except:
                            pass
                        logging.info(f"Nada más que enviar por ahora 1 ")
                        #print(json.dumps(get_borme_info(borme_jstring, requested_zone)))
                        #get_borme_info(borme_jstring, requested_zone)
                        
                        tested_date = datetime.datetime.strptime(requested_date, "%Y-%m-%d")

                        # si no hay borme para una fecha se añade un día a la fecha para la próxima ejecución
                        if tested_date < datetime.datetime.today():
                            logging.info(f"No hay borme para esta fecha")
                            tested_date = tested_date + datetime.timedelta(days=1)
                            yaml_conf['zones'][requested_zone]['last_checked'] = tested_date.strftime("%Y-%m-%d")
                            write_config(yaml_conf)
                            
                            completed_cycle = False
                        else:
                            completed_cycle = True
                else:
                    tested_date = datetime.datetime.strptime(requested_date, "%Y-%m-%d")

                    # si no hay borme para una fecha se añade un día a la fecha para la próxima ejecución
                    if tested_date < datetime.datetime.today():
                        logging.info(f"No hay borme para esta fecha")

                        tested_date = tested_date + datetime.timedelta(days=1)
                        yaml_conf['zones'][requested_zone]['last_checked'] = tested_date.strftime("%Y-%m-%d")
                        write_config(yaml_conf)
                    else:
                        logging.info(f"Nada más que enviar por ahora 2")
                        
                        completed_cycle = True

            # Esperamos x segundos entre cada iteración puesto que va haber pocos cambios entre ejecuciones
            time.sleep(yaml_conf['general']['check_every_s'])