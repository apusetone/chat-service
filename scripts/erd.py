from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph

# Define database URL
DATABASE_URL = "postgresql://postgres:postgres@postgresql:5432/chat_service"

# Create a SQLAlchemy engine instance
engine = create_engine(DATABASE_URL)

# Create a metadata instance
metadata = MetaData()

# Reflect the tables from the database
metadata.reflect(bind=engine)

# Generate the schema graph
graph = create_schema_graph(
    engine=engine,
    metadata=metadata,
    show_datatypes=False,  # Hide the datatypes
    show_indexes=False,    # Hide the indexes
    rankdir='LR',          # Layout from left to right
    concentrate=False      # Do not join the relation lines
)

# Write the schema to a PNG file
graph.write_png('dbschema.png')
