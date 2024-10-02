# This list will contain nodes that are Points of Interest (POIs), which could be used to initialize agents
# and define the routes in those nodes if the graph used is the same that this study uses.
# in those nodes if the graph used is the same that this study uses.
# It will contain the node's 'osmid' of schools, hospitals, universities and important stores of the zone.
POIs = [
    # BIBLIOTECAS / UNIVERSIDADES
    11451712835,
    2008324822,
    2008286650,
    2009547232,
    2009093195,
    4744976959,
    2009093203,
    2845551386,

    # CENTRO SALUD / HOSPITALES
    5881597128,
    358423325,
    2014546928,
    7133340155,

    # COLEGIOS
    5620230109,
    5940544412,
    358423328,
    7136025435,
    2884141237,
    418341182,
    5339486869,
    5320171849,
    11509535055,
    7413722712,
    913101430,

    # CIUDAD JUSTICIA
    9906338365,

    # APARCAMIENTOS
    418340707,
    5258200552,
    5881622802,

    # DEPORTE
    1262964924,
    5881360870,
    1523935339,
    1630132879,
    5341746534,
    5691268375,
    1039172104,
]

# This lists will contain nodes that are common points of entry and exit of the zone, which could be used to
# initialize agents and define the routes in those nodes if the graph used is the same that this study uses.
# It will contain the node's 'osmid' of the main entry and exit points of the zone. (e.g. main avenues, highways)
ENTRY_NODES = [
    # AUTOVÍA DEL GUADALHORCE - SUDESTE
    5535921276,
    349308756,
    250962327,
    # AUTOVIA DEL GUADALHORCE - SUR
    7136025435,
    8372605982,
    1474024113,
    # AUTOVIA DEL GUADALHORCE - SUDOESTE
    577389216,
    1860644935,

    # ESTE
    1039214519,
    1039214752,

    # NORESTE
    1039214643,
    1039214833,

    # NORTE
    2913505648,
    862999676,

    # NOROESTE
    5620230109,
    10083266483,
    2495458054,

    # OESTE
    5224716324,
    351936145,
    21497147,
]

EXIT_NODES = [
    # AUTOVIA DEL GUADALHORCE - SUDESTE
    1524534180,
    914266715,
    352657341,
    913071746,
    3768905390,
    # AUTOVIA DEL GUADALHORCE - SUR
    2009422598,
    8372605982,
    902442635,
    # AUTOVIA DEL GUADALHORCE - SUDOESTE
    7730992829,

    # ESTE
    1039214519,
    1039214752,

    # NORESTE
    5884907266,

    # NORTE
    2913505649,
    862993794,

    # NOROESTE
    5341658085,
    5679579382,
    2430412990,

    # OESTE
    4516839127,
    9613272655,

]
