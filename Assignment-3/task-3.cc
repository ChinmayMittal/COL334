#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/csma-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/ipv4-global-routing-helper.h"

using namespace ns3;
using namespace std;

NS_LOG_COMPONENT_DEFINE ("TestRoutingExample");

/******

                    n4 
                   / 
                  /              
n1 --- n2 ---- n3  ----- n5
                
n1 -----> n4 TCP connection
n2 -----> n5 UDP connection

********/

class MyApp : public Application
{
public:
  MyApp ();
  virtual ~MyApp ();

  /**
   * Register this type.
   * \return The TypeId.
   */
  static TypeId GetTypeId (void);
  void Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate);

private:
  virtual void StartApplication (void);
  virtual void StopApplication (void);

  void ScheduleTx (void);
  void SendPacket (void);

  Ptr<Socket>     m_socket;
  Address         m_peer;
  uint32_t        m_packetSize;
  uint32_t        m_nPackets;
  DataRate        m_dataRate;
  EventId         m_sendEvent;
  bool            m_running;
  uint32_t        m_packetsSent;
};

MyApp::MyApp ()
  : m_socket (0),
    m_peer (),
    m_packetSize (0),
    m_nPackets (0),
    m_dataRate (0),
    m_sendEvent (),
    m_running (false),
    m_packetsSent (0)
{
}

MyApp::~MyApp ()
{
  m_socket = 0;
}

/* static */
TypeId MyApp::GetTypeId (void)
{
  static TypeId tid = TypeId ("MyApp")
    .SetParent<Application> ()
    .SetGroupName ("Tutorial")
    .AddConstructor<MyApp> ()
    ;
  return tid;
}

void
MyApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
MyApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  if (InetSocketAddress::IsMatchingType (m_peer))
    {
      m_socket->Bind ();
    }
  else
    {
      m_socket->Bind6 ();
    }
  m_socket->Connect (m_peer);
  SendPacket ();
}

void
MyApp::StopApplication (void)
{
  m_running = false;

  if (m_sendEvent.IsRunning ())
    {
      Simulator::Cancel (m_sendEvent);
    }

  if (m_socket)
    {
      m_socket->Close ();
    }
}

void
MyApp::SendPacket (void)
{
  Ptr<Packet> packet = Create<Packet> (m_packetSize);
  m_socket->Send (packet);

  if (++m_packetsSent < m_nPackets)
    {
      ScheduleTx ();
    }
}

void
MyApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &MyApp::SendPacket, this);
    }
}

uint32_t maxWindowSize = 0 ; 
static void
CwndChange (Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd, uint32_t newCwnd)
{
  if( newCwnd  > maxWindowSize ) {
    maxWindowSize = newCwnd ; 
  }
  NS_LOG_UNCOND (Simulator::Now ().GetSeconds () << " " << newCwnd);
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << oldCwnd << " " << newCwnd << std::endl;
}

// uint32_t packetDropCount = 0 ;
// static void
// RxDrop (Ptr<const Packet> p)
// {
//   packetDropCount ++ ; 
//   NS_LOG_UNCOND ("RxDrop at " << Simulator::Now ().GetSeconds ());
// }

int main(int argc, char *argv[]) 
{
    LogComponentEnable ("UdpClient", LOG_LEVEL_INFO);
    LogComponentEnable ("UdpServer", LOG_LEVEL_INFO);
    std::string congestionControlAlgorithm = "TcpVegas" ;  
    Ptr<Node> n1 = CreateObject<Node>();
    Ptr<Node> n2 = CreateObject<Node>();
    Ptr<Node> n3 = CreateObject<Node>();
    Ptr<Node> n4 = CreateObject<Node>();
    Ptr<Node> n5 = CreateObject<Node>();

    Names::Add("n1", n1);
    Names::Add("n2", n2);
    Names::Add("n3", n3);
    Names::Add("n4", n4);
    Names::Add("n5", n5);

    NodeContainer n1n2(n1, n2);
    NodeContainer n2n3(n2, n3);
    NodeContainer n3n4(n3, n4);
    NodeContainer n3n5(n3, n5);

    NodeContainer global(n1, n2, n3, n4, n5);

    // create link
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute ("DataRate", StringValue ("500Kbps"));
    p2p.SetChannelAttribute ("Delay", StringValue ("2ms"));

    NetDeviceContainer d1d2 = p2p.Install(n1n2);
    NetDeviceContainer d2d3 = p2p.Install(n2n3);
    NetDeviceContainer d3d4 = p2p.Install(n3n4);
    NetDeviceContainer d3d5 = p2p.Install(n3n5);
    // create internet stack
    InternetStackHelper internet;
    internet.Install (global);

    Ipv4AddressHelper ipv4;

    ipv4.SetBase ("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i1i2 = ipv4.Assign (d1d2);

    ipv4.SetBase ("10.2.2.0", "255.255.255.0");
    Ipv4InterfaceContainer i2i3 = ipv4.Assign (d2d3);

    ipv4.SetBase ("10.3.3.0", "255.255.255.0");
    Ipv4InterfaceContainer i3i4 = ipv4.Assign (d3d4);

    ipv4.SetBase ("10.4.4.0", "255.255.255.0");
    Ipv4InterfaceContainer i3i5 = ipv4.Assign (d3d5);


    Config::SetDefault("ns3::Ipv4GlobalRouting::RandomEcmpRouting",     BooleanValue(true)); // enable multi-path routing
    Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

    // n2 -> n5 UDP connnection
    uint16_t udp_server_port = 4000;
    UdpServerHelper server (udp_server_port);
    ApplicationContainer apps = server.Install (n5);
    apps.Start (Seconds (0.0));
    apps.Stop (Seconds (100.0));

    double interPacketInterval_ = ( (1040.0 * 8 )/(250.0 * 1000) ) ; 
    uint32_t MaxPacketSize = 1040;
    Time interPacketInterval = Seconds (interPacketInterval_); // figure out from application rate
    uint32_t maxPacketCount = 100000;
    UdpClientHelper client (i3i5.GetAddress (1), udp_server_port);
    client.SetAttribute ("MaxPackets", UintegerValue (maxPacketCount));
    client.SetAttribute ("Interval", TimeValue (interPacketInterval));
    client.SetAttribute ("PacketSize", UintegerValue (MaxPacketSize));
    apps = client.Install (n2);
    apps.Start (Seconds (20.0));
    apps.Stop (Seconds (30.0));

    // change data rate
    interPacketInterval_ = ( (1040.0 * 8 )/(500.0 * 1000) ) ; 
    MaxPacketSize = 1040;
    interPacketInterval = Seconds (interPacketInterval_); // figure out from application rate
    maxPacketCount = 100000;
    UdpClientHelper client2 (i3i5.GetAddress (1), udp_server_port);
    client2.SetAttribute ("MaxPackets", UintegerValue (maxPacketCount));
    client2.SetAttribute ("Interval", TimeValue (interPacketInterval));
    client2.SetAttribute ("PacketSize", UintegerValue (MaxPacketSize));
    apps = client2.Install (n2);
    apps.Start (Seconds (30.0));
    apps.Stop (Seconds (100.0));  


    // n1 ----> n4
    uint16_t TCPsinkPort = 8080;

    // TCP-server  
    PacketSinkHelper packetSinkHelper ("ns3::TcpSocketFactory", InetSocketAddress(i3i4.GetAddress(1), TCPsinkPort));
    ApplicationContainer sinkApps = packetSinkHelper.Install (n4);
    sinkApps.Start (Seconds (0.));
    sinkApps.Stop (Seconds (100.)); 

    // TCP client
    // congestion-algorithm setup
    TypeId tid = TypeId::LookupByName ("ns3::" + congestionControlAlgorithm);
    Config::Set ("/NodeList/*/$ns3::TcpL4Protocol/SocketType", TypeIdValue (tid));  
    Ptr<Socket> ns3TcpSocket = Socket::CreateSocket (n1, TcpSocketFactory::GetTypeId ());

    Ptr<MyApp> app = CreateObject<MyApp> ();
    //    ------------------------------ packet-size -- num-paclets-- application-data-rate
    app->Setup (ns3TcpSocket, InetSocketAddress( i3i4.GetAddress(1), TCPsinkPort), 1040, 100000, DataRate ("250Kbps")); 
    n1->AddApplication (app);
    app->SetStartTime (Seconds (1.));
    app->SetStopTime (Seconds (100.));   

    AsciiTraceHelper asciiTraceHelper;
    Ptr<OutputStreamWrapper> stream = asciiTraceHelper.CreateFileStream ("task-3.cwnd");
    ns3TcpSocket->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream));     

    // dump config
    p2p.EnablePcapAll ("task-3");
    
    Simulator::Stop (Seconds (100));
    Simulator::Run ();
    Simulator::Destroy ();

    return 0;
}