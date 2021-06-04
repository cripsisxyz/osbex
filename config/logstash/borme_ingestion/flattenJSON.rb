def register(params)
    @field = params['field']
end

def flatten(object, name, event)
    if object
        if object.kind_of?(Array)
            for i in object do
                if i.kind_of?(Hash) and i != {}
                    i.each { |k, v| flatten(v, "#{name}.#{k}", event) }
                else
                    event.set(name.gsub(" ", "_").gsub(".", "-"), i)
                end
            end
        else
            if object.kind_of?(Hash) and object != {}
                object.each { |k, v| flatten(v, "#{name}.#{k}", event) }
            else
                event.set(name.gsub(" ", "_").gsub(".", "-"), object)
            end    
        end
    end
end

def filter(event)
    o = event.get(@field)
    if o
        flatten(o, @field, event)
    end
    event.remove(@field)
    [event]
end