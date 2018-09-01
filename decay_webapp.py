from flask import Flask, request, g, url_for, \
    render_template, Blueprint
import jinja2
import sqlite3

DATABASE = 'puoliintumisajat/static/atoms.db'

decay_webapp = Blueprint('decay_webapp', __name__, template_folder='templates/atoms',
                         static_folder='static/atoms')

# Database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@decay_webapp.route('/')
@decay_webapp.route('/index.html')
def index():


    c = get_db().cursor()
    c.execute("select distinct atoms.element, elements.name from "
              "(atoms left join  elements on atoms.element = elements.element)"
              "where atoms.id>1 order by elements.name asc;")

    results = [{'chemical':a, 'name':b} for a,b in c.fetchall()]
    rows = [results[i*3:(i*3)+3] for i in range(37)]
    
    return render_template('index.html', atoms=rows)


@decay_webapp.route('/<int:number_z>-<string:atom>-<int:number_a>')
def atom_full(number_z, atom, number_a):
    q_element = upper_first(atom)

    search = '{}-{}-{}'.format(number_z,atom,number_a)

    return fetch_results('select * from atoms LEFT JOIN elements ON '
                         'atoms.element = elements.element '
                         'where atoms.element = ? and mass = ? '
                         'and protons = ?', (q_element, number_a, number_z), search)

@decay_webapp.route('/<int:number>-<int:number2>')
def atom_between(number, number2):
    if number2 < number:
        temp = number2
        number2 = number
        number = temp

    search = '{}-{}'.format(number, number2)
    
    return fetch_results('select * from atoms LEFT JOIN elements ON '
                         'atoms.element = elements.element '
                         'where mass between ? and ?', (number,number2), search)


@decay_webapp.route('/<int:number>-<string:atom>')
@decay_webapp.route('/<string:atom>-<int:number>')
def atom_partial(number, atom):
    q_element = upper_first(atom)

    search = '{}-{}'.format(atom, number)
    return fetch_results('select * from atoms LEFT JOIN elements ON '
                         'atoms.element = elements.element '
                         'where atoms.element = ? '
                         'and (mass = ? or protons = ?)', (q_element, number,number),
                         search)



@decay_webapp.route('/<int:number>')
def atom_number(number):

    search = '{}'.format(number)
    return fetch_results('select * from atoms LEFT JOIN elements ON '
                         'atoms.element = elements.element '
                         'where protons = ? or mass = ?', (number,number), search)

@decay_webapp.route('/<string:element>')
def atom_element(element):
    search = '{}'.format(element)
    if(len(element)<3):
        q_element = upper_first(element)



        return fetch_results('select * from atoms LEFT JOIN elements ON '
                             'atoms.element = elements.element '
                             'where atoms.element = ?', (q_element,), search)
    else:
        return fetch_results('select * from atoms LEFT JOIN elements ON '
                             'atoms.element = elements.element '
                             'where elements.name LIKE ?', (element,), search)

# Seuraavat ovat sitten apufunkkareita
def upper_first(text):
    """Muuntaa annetussa tekstipätkässä ensimmäisen kirjaimen isolla ja muut pienellä"""
    all_ups = text.upper()
    
    if len(all_ups) <= 1:
        return all_ups
    
    return all_ups[0] + all_ups[1:].lower()



def query_db(query, args=(), one=False):
    """Simply query-helper function, code "borrowed" from flask website"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def fetch_results(query, args=(), search_terms=''):
    c = get_db().cursor()
    c.execute(query, args)
    results = c.fetchall()

    if results:
        try: 
            text = render_template('elements.html', elements=tidy_results(results),
                                   search_term=search_terms)
        except jinja2.TemplateSyntaxError as e:
            print('Tässä on nyt virhe "{}" rivillä "{}"'.format(e.message, e.lineno))

        return text
    else:
        return render_template('notfound.html')


DECAYDIC = {'Beta': 'beeta-',
            'EC': 'elektronisieppaus ja/tai beeta+',
            'IT': 'sisäinen konversio', 
            'Alpha': 'alfahajoaminen',
            'Neutron': 'neutroniemissio',
            'P':'protoniemissio'}


def fetch_decays(parent_nuclide):
    c = get_db().cursor()
    
    c.execute('select atoms.protons, atoms.element, atoms.mass, atoms.radioactive,'
              ' atoms.isomere, decaymode.decays, decaymode.fraction, elements.name'
              ' from decaymode left join atoms on (atoms.id=decaymode.daughter and'
              ' decaymode.isomere=atoms.isomere)'
              ' left join elements on atoms.element = elements.element where atom_id = ?'
              ' order by decaymode.fraction desc',
              (parent_nuclide,))


    rows = c.fetchall()

    def tidy_row(row):

        mass = row[2]
        atom = row[1]
        protons = row[0]
        radioactive = 'Stabiili' if row[3] == 1 else 'Epästabiili'
        fraction = row[6]
        if fraction < 0.001:
            percentage = '{:0.3E}/1'.format(fraction)
        else:
            percentage = '{:0.1f} %'.format(fraction*100)
        decays = [DECAYDIC[item.strip()] for item in row[5].split(',')]
        decays = ', '.join(decays)
        element = row[7]

        results = {'percentage':percentage, 'decays':decays, 'mass':mass, 'protons':protons,
                'atom':atom, 'element':element}
        if row[4] != 0:
            results['isomere']= True

        return results
        

    return [tidy_row(row) for row in rows]


def fetch_parents(daughter_nuclide):

    c = get_db().cursor()
    c.execute('select atoms.protons, atoms.element, atoms.mass, atoms.radioactive,'
              ' atoms.isomere, decaymode.decays, decaymode.fraction, elements.name'
              ' from decaymode left join atoms on (atoms.id=decaymode.atom_id)'
              ' left join elements on atoms.element = elements.element where daughter = ?'
              ' order by atoms.element',
              (daughter_nuclide,))

    rows =  c.fetchall()

    def tidy_row(row):

        mass = row[2]
        atom = row[1]
        protons = row[0]
        radioactive = 'Stabiili' if row[3] == 1 else 'Epästabiili'
        fraction = row[6]
        if fraction < 0.001:
            percentage = '{:0.3E}'.format(fraction)
        else:
            percentage = '{:0.1f} %'.format(fraction*100)
        decays = [DECAYDIC[item.strip()] for item in row[5].split(',')]
        decays = ', '.join(decays)
        element = row[7]

        results = {'percentage':percentage, 'decays':decays, 'mass':mass, 'protons':protons,
                'atom':atom, 'element':element}
        if row[4] != 0:
            results['isomere']= True

        return results

    return [tidy_row(row) for row in rows]

    
def tidy_results(results):
    """Muuntaan sql:n saadun tulosrivin jinja-templatelle sopivaksi"""


    def tidy_row(row, i):

        mass = row[3]
        protons = row[1]        
        atom = row[2]
        
        halflife = "puoliintumisaika: " + pretty_time(row[-3]) if row[-4]==1 else 'Stabiili'
        element = row[-1]
        
        collapse = "collapse_" + str(i)
        row_id = "heading_" + str(i)

        daughters = fetch_decays(row[0])
        parents = fetch_parents(row[0])

        endresults = {'atom':atom, 'mass':mass, 'protons':protons, 'element':element,
                      'halflife':halflife, 'collapse':collapse, 'id':row_id,
                      'daughters':daughters, 'parents':parents}
        if row[-4] == 1:
            endresults['unstable'] = True
        if row[4] != 0:
            endresults['isomere'] = 'm'
        else:
            endresults['isomere'] = ''
            

        return endresults

    all_atoms = set([row[-1] for row in results])

    elements = {}
    end_results = []

    big_i = 1

    for atom in all_atoms:
        elements = {}
        elements['element'] = upper_first(atom)
        atom_results = [row for row in results if row[-1]==atom]
        mid_results = [tidy_row(row, i + big_i) for i, row in enumerate(atom_results)]
        big_i += len(mid_results)
        elements['rows'] = mid_results
        end_results.append(elements)

    return end_results


def pretty_time(seconds):
    if seconds < 1e-9:
        return "{:0.2E} s".format(seconds)
    elif seconds < 1e-6:
        return "{:0.1f} ns".format(1e9*seconds)
    elif seconds < 1e-3:
        return "{:0.1f} &mu;s".format(1e6*seconds)
    elif seconds < 1:
        return "{:0.1f} ms".format(1e3*seconds)
    elif seconds < 100:
        return "{:0.1f} s".format(seconds)
    elif seconds < 3600:
        return "{:0.1f} min".format(seconds/60)
    elif seconds < 86400: # day
        return "{:0.1f} h".format(seconds/3600)
    elif seconds < 31557600.0: # year
        return "{:0.1f} d".format(seconds/86400)
    elif seconds < 3155760000000: # year
        return "{:0.0f} y".format(seconds/31557600.0)
    else:
        return "{:0.2E} y".format(seconds/31557600.0)


if __name__ == '__main__':
    app.run()


    
