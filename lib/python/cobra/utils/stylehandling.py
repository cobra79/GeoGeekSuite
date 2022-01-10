import cobra.helper.logging as logging

class Stylecreator():

    def __init__(self):

        self.l = logging.Logger(self)
        self.stylepath = '/styles'

    def create_style(self, stylename, style_def):
        
        self.l.debug('create_style: {stylename}')
        with open(f"{self.stylepath}/{stylename}.style", "w") as f:
            for a_row in style_def:
                f.write(f"{a_row['OsmType']}\t{a_row['Tag']}\t{a_row['DataType']}\t{a_row['Flags']}\n")

    def attribute_list_to_style_def(self, attribute_list):

        self.l.debug('attribute_list_to_style_def')
    
        styles = []
        for an_attribute in attribute_list:
            styles.append({
                    'OsmType':'node,way',
                    'Tag': an_attribute,
                    'DataType':'text',
                    'Flags':'linear'
            })
        return styles

    def create_style_from_attribute_list(self, stylename, attribute_list):

        self.l.debug('create_style_from_attribute_list')

        style_def = self.attribute_list_to_style_def(attribute_list)
        self.create_style(stylename, style_def)
