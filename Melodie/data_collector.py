import time
from typing import List, ClassVar, TYPE_CHECKING, Dict, Tuple, Any, Optional

import pandas as pd
import logging

from Melodie.db import DB

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from Melodie import Model
    from Melodie.agent_list import BaseAgentContainer


class PropertyToCollect:
    """
    It is property to collect.
    stores class and
    """

    def __init__(self, property_name: str, as_type: ClassVar):
        self.property_name = property_name
        self.as_type = as_type


class DataCollector:
    """
    Data Collector collects data for each scenario.
    At the beginning of simulation scenario, the DataCollector creates;
    User could customize which data should be dumped to dataframe.
    By simulation scenario exits, the DataCollector dumps the data to dataframe, and save to
    data or datafile.
    """

    def __init__(self, target='sqlite'):
        assert target in {'sqlite', None}, f"Invalid database type {target}"
        self.target = target
        self.model: Optional[Model] = None
        self._agent_properties_to_collect: Dict[str, List[PropertyToCollect]] = {}
        self._environment_properties_to_collect: List[PropertyToCollect] = []

        self.agent_properties_df = pd.DataFrame()
        self.environment_properties_df = pd.DataFrame()

        self.agent_properties_dict: Dict[str, List[Any]] = {}
        self.environment_properties_list = []

        self._time_elapsed = 0

    def setup(self):
        pass

    def add_agent_property(self, container_name: str, property_name: str, as_type: ClassVar = None):
        """
        This method tells the data collector which property and in which agent container it should collect.
        It can also be determined what type the data could be represented as in the database.
        :param container_name:
        :param property_name:
        :param as_type:
        :return:
        """
        if not hasattr(self.model, container_name):
            raise AttributeError(f"Model has no agent container '{container_name}'")
        if container_name not in self._agent_properties_to_collect.keys():
            self._agent_properties_to_collect[container_name] = []
        self._agent_properties_to_collect[container_name].append(PropertyToCollect(property_name, as_type))

    def add_environment_property(self, property_name: str, as_type: ClassVar = None):
        """
        This method tells the data collector which property of environment should be collected.
        :param property_name:
        :param as_type:
        :return:
        """
        self._environment_properties_to_collect.append(PropertyToCollect(property_name, as_type))

    def env_property_names(self):
        """

        :return:
        """
        return [prop.property_name for prop in self._environment_properties_to_collect]

    def agent_property_names(self):
        """

        :return:
        """
        return {container_name: [prop.property_name for prop in props] for container_name, props in
                self._agent_properties_to_collect.items()}

    def agent_containers(self) -> List[Tuple[str, 'BaseAgentContainer']]:
        """

        :return:
        """
        containers = []
        for container_name in self._agent_properties_to_collect.keys():
            containers.append((container_name, getattr(self.model, container_name)))
        return containers

    def collect_agent_properties(self, step: int, run_id: int, scenario_id: int):
        """

        :param step:
        :param run_id:
        :param scenario_id:
        :return:
        """
        agent_containers = self.agent_containers()
        agent_property_names = self.agent_property_names()
        for container_name, container in agent_containers:
            agent_prop_list = container.to_list(agent_property_names[container_name])
            for agent_prop in agent_prop_list:
                agent_prop['step'] = step
                agent_prop['run_id'] = run_id
                agent_prop['scenario_id'] = scenario_id
            if container_name not in self.agent_properties_dict:
                self.agent_properties_dict[container_name] = []
            self.agent_properties_dict[container_name].extend(agent_prop_list)

    def collect(self, step: int):
        """
        The main function to collect data.
        :param step:
        :return:
        """
        t0 = time.time()
        env = self.model.environment

        scenario = self.model.scenario
        run_id = self.model.run_id_in_scenario
        env_dic = env.to_dict(self.env_property_names())
        env_dic['step'] = step
        env_dic['scenario_id'] = scenario.id
        env_dic['run_id'] = run_id

        self.environment_properties_list.append(env_dic)

        self.collect_agent_properties(step, run_id, scenario.id)
        t1 = time.time()
        self._time_elapsed += (t1 - t0)

    def save(self):
        """
        Save the collected data into database.
        :return:
        """
        t0 = time.time()

        environment_properties_df = pd.DataFrame(self.environment_properties_list)
        self.model.create_db_conn().write_dataframe(DB.ENVIRONMENT_RESULT_TABLE, environment_properties_df, {})

        for container_name in self.agent_properties_dict.keys():
            agent_properties_df = pd.DataFrame(self.agent_properties_dict[container_name])
            self.model.create_db_conn().write_dataframe(container_name + "_result", agent_properties_df, {})

        t1 = time.time()
        collect_time = self._time_elapsed
        db_wrote_time = t1 - t0
        self._time_elapsed += db_wrote_time
        logger.info(f'datacollector took {t1 - t0}s to format dataframe and write it to data.\n'
                    f'    {db_wrote_time} for writing into database, and {collect_time} for collect data.')
