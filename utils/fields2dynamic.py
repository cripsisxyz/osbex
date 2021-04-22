## Pequeña utilidad para generar texto dinámico para el panel de dynamictext de grafana

import re

if __name__ == "__main__":

    with open('dynamic_text_fields.txt') as f:
        for line in f:
            newoutput = f"{{{{#if {line.strip()}}}}}"

            restring = line.strip().replace("actos-", "")
            

            if re.match(r'\w+-.*', restring):
                cutstring = restring.split("-", 1)

                newoutput = f"{newoutput}\n**- {cutstring[0].replace('_', ' ')} del/la {cutstring[1].replace('-', '.').replace('_', '')}**:\n\n{{{{{line.strip()}}}}}"
            else:
                
                newoutput = f"{newoutput}\n**- {restring.replace('_', ' ')}**:\n\n{{{{{line.strip()}}}}}"
            
            newoutput = f"{newoutput}\n{{{{/if}}}}\n"

            print(newoutput)