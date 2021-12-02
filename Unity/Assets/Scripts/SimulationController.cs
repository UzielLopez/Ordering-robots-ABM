using System.Collections;
using System.Collections.Generic;
using UnityEngine.Networking;
using UnityEngine;
using Newtonsoft.Json;

[System.Serializable]

public class IDManager
{
    public int[] robots;
    public int[] boxes;
    public int[] shelves;

}
public class Agent
{
    public Agent(int id)
    {
        this.id = id;
    }

    public void instantiate3DModel(GameObject instance)
    {
        agent3DModel = instance;
    }

    public GameObject agent3DModel;
    public int x = 0, z = 0, id;
}

public class Robot : Agent
{
    public Robot(int id) : base(id) { }
    public GameObject box3DModel = null;
    public float DELTA_X = 0.5f, DELTA_Z = 0.15f;
    public float BOX_DELTA_X = -0.336f, BOX_DELTA_Y = 0.1f, BOX_DELTA_Z = 0.635f;
    public bool carryingBox = false, wasCarryingBoxAlready;
}

public class Shelf : Agent
{
    public Shelf(int id) : base(id) { }
    public List<GameObject> box3DModels = new List<GameObject>();
    public int deltaBoxes = 0, boxes = 0;
    public float BOX_DELTA_X = 0.15f, BOX_DELTA_Y = 0.3f, BOX_DELTA_Z = 0.65f;
}

public class Box : Agent
{
    public Box(int id) : base(id) { }
    public float DELTA_X = 0.0f, DELTA_Z = 0.3f;
    public bool carryingBox = false;
    public bool stillInSimulation = false;
}


public class SimulationController : MonoBehaviour
{
    public GameObject robot, box, shelf, floorTile;
    public int k = 10, m = 6, n = 6, timeLimit = 100;
    private int steps = 0;
    private bool simulationFinished = false, allBoxesCleared = false;
    private float timer = 0.0f;
    private float waitTime = 0.5f;
    private string simulationURL;
    public Dictionary<int, Robot> robots;
    public Dictionary<int, Shelf> shelves;
    public Dictionary<int, Box> boxes;

    // Start is called before the first frame update

    void Start()
    {

        StartCoroutine(PrepareSimulation());

    }

    // Update is called once per frame
    void Update()
    {
        timer += Time.deltaTime;
        if(timer > waitTime && !simulationFinished)
        {
            StartCoroutine(FetchAgentsData());
            timer = timer - waitTime;
        }
        
        if(simulationFinished)
        {
            if(allBoxesCleared)
            {
                Debug.Log("All boxes where put in shelves in" + steps.ToString() + " steps" + "--- Sum of steps taken by all the agents: " + (steps*5).ToString());
            }

            else
            {
                Debug.Log("The robots couldn't place all the boxes in shelves.");
            }
            
        }
    }

    void InstantiateAgents(string idsForAgents, string initialState)
    {

        IDManager idManager = JsonUtility.FromJson<IDManager>(idsForAgents.Replace("'", "\""));
        Dictionary<int, int[]> positions = JsonConvert.DeserializeObject<Dictionary<int, int[]>>(initialState);

        robots = new Dictionary<int, Robot>();
        shelves = new Dictionary<int, Shelf>();
        boxes = new Dictionary<int, Box>();

        foreach (var id in idManager.robots)
        {
            robots[id] = new Robot(id);
            robots[id].x = positions[id][0];
            robots[id].z = positions[id][1];
            robots[id].instantiate3DModel(Instantiate(robot, new Vector3(robots[id].x + robots[id].DELTA_X, 0, robots[id].z + robots[id].DELTA_Z), Quaternion.identity));
        }

        foreach (var id in idManager.shelves)
        {
            shelves[id] = new Shelf(id);
            shelves[id].x = positions[id][0];
            shelves[id].z = positions[id][1];
            shelves[id].instantiate3DModel(Instantiate(shelf, new Vector3(shelves[id].x, 0, shelves[id].z), Quaternion.identity));
        }

        foreach (var id in idManager.boxes)
        {
            boxes[id] = new Box(id);
            boxes[id].x = positions[id][0];
            boxes[id].z = positions[id][1];
            boxes[id].instantiate3DModel(Instantiate(box, new Vector3(boxes[id].x + boxes[id].DELTA_X, 0, boxes[id].z + boxes[id].DELTA_Z), Quaternion.identity));
        }

        for (int i = 0; i < m; i++)
        {
            for (int j = 0; j < n; j++)
            {
                Instantiate(floorTile, new Vector3(i, 0, j), Quaternion.identity);
            }
        }

    }

    IEnumerator PrepareSimulation()
    {
        WWWForm form = new WWWForm();
        string idsForAgents = null;
        form.AddField("numberOfBoxes", k.ToString());
        form.AddField("columns", m.ToString());
        form.AddField("rows", n.ToString());
        form.AddField("timeLimit", timeLimit.ToString());

        using (UnityWebRequest www = UnityWebRequest.Post("http://127.0.0.1:5000/createModel", form))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }

            else
            {
                idsForAgents = www.GetResponseHeader("IdsForAgents");
                simulationURL = www.GetResponseHeader("Location");
            }


        }

        using (UnityWebRequest www = UnityWebRequest.Get(simulationURL))
        {
            yield return www.SendWebRequest();

            if (simulationURL == null)
            {
                Debug.Log(www.error);
            }

            else
            {
                InstantiateAgents(idsForAgents, www.downloadHandler.text);
            }


        }
    }

    IEnumerator FetchAgentsData()
    {
        using (UnityWebRequest www = UnityWebRequest.Get(simulationURL))
        {
            if (simulationURL != null)
            {
                yield return www.SendWebRequest();
                string response = www.downloadHandler.text;
                Dictionary<int, int[]> agentData = JsonConvert.DeserializeObject<Dictionary<int, int[]>>(response);

                foreach (KeyValuePair<int, int[]> datum in agentData)
                {
                    
                    if(robots.ContainsKey(datum.Key))
                    {
      
                        robots[datum.Key].x = datum.Value[0];
                        robots[datum.Key].z = datum.Value[1];
                        robots[datum.Key].wasCarryingBoxAlready = robots[datum.Key].carryingBox;
                        robots[datum.Key].carryingBox = System.Convert.ToBoolean(datum.Value[2]);
                    }

                    if (boxes.ContainsKey(datum.Key))
                    {
                        boxes[datum.Key].stillInSimulation = true;
                    }

                    if (shelves.ContainsKey(datum.Key))
                    {
                        shelves[datum.Key].deltaBoxes = datum.Value[2] - shelves[datum.Key].boxes;
                        shelves[datum.Key].boxes = datum.Value[2];
                    }
                }

                simulationFinished = System.Convert.ToBoolean(agentData[-1][0]);
                steps = agentData[-1][1];
                allBoxesCleared = System.Convert.ToBoolean(agentData[-1][2]);
                
            }
            
        }
       
        ProcessAgentData();

    }


    void ProcessAgentData()
    {
        foreach(Robot robot in robots.Values)
        {
            robot.agent3DModel.transform.position = new Vector3(robot.x + robot.DELTA_X, 0, robot.z + robot.DELTA_Z);
            if(robot.carryingBox)
            {
                Vector3 newBoxPosition = robot.agent3DModel.transform.position + new Vector3(robot.BOX_DELTA_X, robot.BOX_DELTA_Y, robot.BOX_DELTA_Z);
                if (robot.box3DModel == null)
                {
                    robot.box3DModel = Instantiate(box, newBoxPosition, Quaternion.identity);
                }

                else
                {
                    robot.box3DModel.transform.position = newBoxPosition;
                }
            }

            // This means the robot left its corresponding box in its place
            else if(robot.wasCarryingBoxAlready && !robot.carryingBox)
            {
                Destroy(robot.box3DModel);
            }


        }

        foreach (Box box in boxes.Values)
        {
            if(box.stillInSimulation)
            {
                box.stillInSimulation = false;
                continue;
            }

            Destroy(box.agent3DModel);

        }

        foreach (Shelf shelf in shelves.Values)
        {
            for(int i = 0; i < shelf.deltaBoxes; i++)
            {
                Debug.Log((shelf.BOX_DELTA_Y * (shelf.boxes - 1)).ToString());
                shelf.box3DModels.Add(Instantiate(box, new Vector3(shelf.x + shelf.BOX_DELTA_X, (shelf.BOX_DELTA_Y * (shelf.boxes - 1)) - (i * shelf.BOX_DELTA_Y), shelf.z + shelf.BOX_DELTA_Z), Quaternion.identity));
            }
        }
    }
}