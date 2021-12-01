from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

from random import randint

from .a_star import a_star
from .bfs import find_closest_box

class Shelf(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.model = model
        self.position = pos
        self.boxes = 0
        self.filled = False

    def add_box(self):

        if self.filled:
            return False

        self.boxes += 1
        if self.boxes == 5:
            self.marked_self_as_filled()
        return True

    def marked_self_as_filled(self):
        self.filled = True
        self.model.shelves_positions.remove(self.position)
    
    def step(self):
        pass

class Box(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.position = pos
    
    def delete_self_from_model(self):
        self.model.boxes_positions.remove(self.position)
        self.model.state.pop(str(self.unique_id))
        self.model.grid.remove_agent(self)
        self.model.scheduler.remove(self)

    def step(self):
        pass

class Robot(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.position = pos
        self.carrying_box = False
        self.stopped = False
        self.target_position = find_closest_box(self.position, self.model.m, self.model.n, self.model.boxes_positions)
        self.camino = a_star(self.position, self.target_position, self.model.m, self.model.n, self.model.shelves_positions)[1:]
        
    
    # We prioritze those shelves that are almost full to try to form as many filled shelves as quickly as possible
    def find_closest_to_be_filled_shelf_position(self):
        positions = []
        for position in self.model.shelves_positions:
            for content in self.model.grid.iter_cell_list_contents(position):
                if type(content) == Shelf:
                    positions.append(content.position)
        return max(positions)

    def step(self):

        if not self.stopped:

            self.position = self.camino[0]
            self.camino.pop(0)

            if self.position == self.target_position:
                
                if not self.carrying_box:
                    
                    for content in self.model.grid.iter_cell_list_contents(self.position):
                        if type(content) == Box:
                            self.carrying_box = True
                            content.delete_self_from_model()
                            self.target_position = self.find_closest_to_be_filled_shelf_position()
                            tmp_blocks = self.model.shelves_positions.copy()
                            tmp_blocks.remove(self.target_position)
                            self.camino = a_star(self.position, self.target_position, self.model.m, self.model.n, tmp_blocks)[1:]
                            self.model.grid.move_agent(self, self.position)
                            return

                    # If this robot couldn't pick the targeted box because another one picked it first, find another one
                    if not self.carrying_box:
                        self.target_position = find_closest_box(self.position, self.model.m, self.model.n, self.model.boxes_positions)
                        if self.target_position == (-1, -1):
                            self.stopped = True
                            self.model.grid.move_agent(self, self.position)
                            return
                        self.camino = a_star(self.position, self.target_position, self.model.m, self.model.n, self.model.shelves_positions)[1:]
            
                if self.carrying_box:
                    
                    for content in self.model.grid.iter_cell_list_contents(self.position):
                        
                        if type(content) == Shelf:
                            if content.add_box(): #If the box could be placed, go find another one
                                
                                self.model.placed_boxes += 1
                                self.carrying_box = False
                                
                                tmp_blocks = self.model.shelves_positions.copy()

                                if content.position in tmp_blocks: # Make sure that the shelf wasn't filled before you riched it
                                    tmp_blocks.remove(content.position)

                                self.target_position = find_closest_box(self.position, self.model.m, self.model.n, self.model.boxes_positions)
                                # If there are no more boxes to pick, stop!
                                if self.target_position == (-1, -1):
                                    self.stopped = True
                                    self.model.grid.move_agent(self, self.position)
                                    return

                                
                                self.camino = a_star(self.position, self.target_position, self.model.m, self.model.n, tmp_blocks)[1:]
                                
                            
                            else: #If the box couldn't be placed (because another robot filled the shelf before this robot could place it)
                                
                                self.target_position = self.find_closest_to_be_filled_shelf_position()
                                tmp_blocks = self.model.shelves_positions.copy()
                                tmp_blocks.remove(self.target_position)
                                self.camino = a_star(self.position, self.target_position, self.model.m, self.model.n, tmp_blocks)[1:]



            self.model.grid.move_agent(self, self.position)

class Warehouse(Model):
    def __init__(self, k, m, n, time_limit):
        super().__init__()

        self.k = k
        self.placed_boxes = 0
        self.m = m
        self.n = n
        self.time_limit = time_limit
        self.steps_taken = 0

        self.state = {}
        self.initial_state = {}
        self.ids_by_agent_type = {"robots": [], "shelves": [], "boxes": []}
        

        self.grid = MultiGrid(m, n, False)
        self.scheduler = RandomActivation(self)
        
        
        self.enough_space_for_agents = False
        self.boxes_positions = set()
        self.shelves_positions = set()
        self.layout_agents() # TODO: Hacer algo si no hay espacio suficiente
        self.order_agent_ids()
        self.construct_model_initial_state()
        #self.construct_model_state()
        self.blocks = set.union(self.boxes_positions, self.shelves_positions)
        
    
    def layout_agents(self):
        
        non_empty_positions = set()
        
        # Calculate how many shelves we need to store all the boxes
        needed_shelves = (self.k // 5) + 1
        
        # Check if there are enough tiles to place all the agents
        if(self.m*self.n >= 5 + self.k + needed_shelves):
            self.enough_space_for_agents = True
        else:
            return
            
        
        # Layout shelves
        vertically_or_horizontally = False # Vertically is True, horizontally is False
        if(self.m < self.n):
            vertically_or_horizontally = True
            
        
        if vertically_or_horizontally:
            for i in range(self.n):
                pos = (0, i)
                non_empty_positions.add(pos)
                self.shelves_positions.add(pos)
                shelf = Shelf(self, pos)
                self.grid.place_agent(shelf, pos)
                self.scheduler.add(shelf)
                needed_shelves = needed_shelves - 1
                if needed_shelves == 0:
                    break
                pos = (self.m - 1, i)
                non_empty_positions.add(pos)
                self.shelves_positions.add(pos)
                shelf = Shelf(self, pos)
                self.grid.place_agent(shelf, pos)
                self.scheduler.add(shelf)
                needed_shelves = needed_shelves - 1
                if needed_shelves == 0:
                    break
        else:
            for i in range(self.m):
                pos = (i, 0)
                non_empty_positions.add(pos)
                self.shelves_positions.add(pos)
                shelf = Shelf(self, pos)
                self.grid.place_agent(shelf, pos)
                self.scheduler.add(shelf)
                needed_shelves = needed_shelves - 1
                if needed_shelves == 0:
                    break
                pos = (i, self.n -1)
                non_empty_positions.add(pos)
                self.shelves_positions.add(pos)
                shelf = Shelf(self, pos)
                self.grid.place_agent(shelf, pos)
                self.scheduler.add(shelf)
                needed_shelves = needed_shelves - 1
                if needed_shelves == 0:
                    break
        
        # Layout boxes
        for i in range(self.k):
            
            pos = (randint(0, self.m - 1), randint(0, self.n - 1))
            while pos in non_empty_positions:
                pos = (randint(0, self.m - 1), randint(0, self.n - 1))
            non_empty_positions.add(pos)
            self.boxes_positions.add(pos)
            box = Box(self, pos)
            self.grid.place_agent(box, pos)
            self.scheduler.add(box)
        
        # Layout robots
        for _ in range(5):
            
            pos = (randint(0, self.m - 1), randint(0, self.n - 1))
            while pos in non_empty_positions:
                pos = (randint(0, self.m - 1), randint(0, self.n - 1))
            non_empty_positions.add(pos)
            robot = Robot(self, pos)
            self.grid.place_agent(robot, pos)
            self.scheduler.add(robot)

    def simulation_finished(self):
        return self.placed_boxes == self.k or self.time_limit == self.steps_taken
    
    def construct_model_initial_state(self):
        for agent in self.scheduler.agents:
            if type(agent) == Robot:
                self.state[str(agent.unique_id)] = agent.pos
            elif type(agent) == Shelf:
                self.state[str(agent.unique_id)] = agent.pos
            elif type(agent) == Box:
                self.state[str(agent.unique_id)] = agent.pos

    def construct_model_state(self):
        for agent in self.scheduler.agents:
            if type(agent) == Robot:
                self.state[str(agent.unique_id)] = [agent.pos[0], agent.pos[1], int(agent.carrying_box)]
            elif type(agent) == Shelf:
                self.state[str(agent.unique_id)] = [agent.pos[0], agent.pos[1], agent.boxes]
            elif type(agent) == Box:
                self.state[str(agent.unique_id)] = agent.pos

    def order_agent_ids(self):
        for agent in self.scheduler.agents:
            if type(agent) == Robot:
                self.ids_by_agent_type["robots"].append(agent.unique_id)
            elif type(agent) == Shelf:
                self.ids_by_agent_type["shelves"].append(agent.unique_id)
            elif type(agent) == Box:
                self.ids_by_agent_type["boxes"].append(agent.unique_id)
            
        
    def step(self):
        
        if not self.simulation_finished():
            self.scheduler.step()
            self.construct_model_state()
            self.steps_taken += 1
        

def agent_portrayal(agent):
    if type(agent) == Box:
        portrayal = {"Shape": "rect", "Filled": "true", "Color": "#995943", "w": 0.45, 'h': 0.45, "Layer": 0}
    elif type(agent) == Robot:
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "Blue", "r": 0.55, "Layer": 0}
    elif type(agent) == Shelf:
        portrayal = {"Shape": "rect", "Filled": "true", "Color": "Gray", "w": 0.45, 'h': 0.45, "Layer": 0}
    else:
        portrayal = {}

    return portrayal

"""
k = 10
m = 5
n = 6
time_limit = 50
grid = CanvasGrid(agent_portrayal, m, n, 450, 450)
server = ModularServer(Warehouse, [grid], "Actividad integradora", {'k': k, 'm': m, 'n': n, 'time_limit':time_limit})
server.port = 8522
server.launch()
"""

