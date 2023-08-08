namespace RacePredictor.Core;

public class RaceEntity
{
    public RaceEntity(int id, string name)
    {
        Id = id;
        Name = name;
    }

    public int Id { get; }
    public string Name { get; }
}
