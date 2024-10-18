"""
Evaluator workflow to Load and Filter Data Sets, Estimate Data Sets, Analyze Data Sets
Applied to calculations of Heats of Mixing and Density of Water.
"""

# Core Imports & Setup

import os
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("openff.toolkit").setLevel(logging.ERROR)


# 1) Loading data sets

## Extracting Data from ThermoML or json file 
from openff.evaluator.datasets import PhysicalProperty, PropertyPhase, PhysicalPropertyDataSet
from openff.evaluator.datasets.thermoml import thermoml_property, ThermoMLDataSet

# 2) Estimating data sets

## Loading data set and applying FF parameters
from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.toolkit.typing.engines.smirnoff import forcefield, ForceField

### load data
data_set_path = Path('filtered_dataset_hmix_dens.json')
data_set = PhysicalPropertyDataSet.from_json(data_set_path)

### load FF
force_field = ForceField("openff-2.1.0.offxml", "tip3p_fb.offxml")
with open("force-field.json", "w") as file:
    file.write(SmirnoffForceFieldSource.from_object(force_field).json())

force_field_source = SmirnoffForceFieldSource.from_json("force-field.json")

## Defining calculation Schemas
from openff.evaluator.properties import Density, EnthalpyOfMixing
from openff.evaluator.client import RequestOptions

### Create an options object which defines how the data set should be estimated.
estimation_options = RequestOptions.from_json('options.json')

## Launching a Server and Client
from openff.evaluator.backends import ComputeResources
from openff.evaluator.backends.dask import DaskLocalCluster
from openff.evaluator.server import EvaluatorServer
from openff.evaluator.client import EvaluatorClient
from openff.evaluator.client import ConnectionOptions

### define client to submit queries
port = 8118
evaluator_client = EvaluatorClient(ConnectionOptions(server_port=port))

### define available / preferred resources
resources = ComputeResources(
    number_of_threads=1,
    number_of_gpus=1,
    preferred_gpu_toolkit=ComputeResources.GPUToolkit.CUDA,
)

with DaskLocalCluster(number_of_workers=1, resources_per_worker=resources) as calculation_backend:
    ### spin up server
    evaluator_server = EvaluatorServer(calculation_backend=calculation_backend, delete_working_files=False, port=port)
    evaluator_server.start(asynchronous=True)

    ### estimate data set by submitting calculation schemas to newly-created server
    request, exception = evaluator_client.request_estimate(
        property_set=data_set,
        force_field_source=force_field_source,
        options=estimation_options,
    )

    ### Wait for the results.
    results, exception = request.results(synchronous=True, polling_interval=30)
    assert exception is None

    a = results.estimated_properties.json("estimated_dataset_hmix_dens.json", format=True)
    print(a)
