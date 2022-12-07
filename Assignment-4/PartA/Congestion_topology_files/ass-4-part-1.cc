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

static void
CwndChange (Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd, uint32_t newCwnd)
{

  NS_LOG_UNCOND (Simulator::Now ().GetSeconds () << " " << newCwnd);
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << oldCwnd << " " << newCwnd << std::endl;
}

int main(int argc, char *argv[]) 
{

    Ptr<Node> n1 = CreateObject<Node>();
    Ptr<Node> n2 = CreateObject<Node>();
    Ptr<Node> n3 = CreateObject<Node>();
    std::string congestionControlAlgorithm = "TcpNewRenoPlus" ;
    uint32_t packetSize = 3000 ;  
    std::string applicationDataRate = "1.5Mbps" ;
    Names::Add("n1", n1);
    Names::Add("n2", n2);
    Names::Add("n3", n3);

    NodeContainer n1n3(n1, n3);
    NodeContainer n2n3(n2, n3); 

    NodeContainer global(n1, n2, n3);

    // create link
    PointToPointHelper p2p1, p2p2;
    // first link
    p2p1.SetDeviceAttribute ("DataRate", StringValue ("10Mbps"));
    p2p1.SetChannelAttribute ("Delay", StringValue ("3ms"));

    //second link
    p2p2.SetDeviceAttribute ("DataRate", StringValue ("9Mbps"));
    p2p2.SetChannelAttribute ("Delay", StringValue ("3ms"));

    NetDeviceContainer d1d3 = p2p1.Install(n1n3);
    NetDeviceContainer d2d3 = p2p2.Install(n2n3);

    Ptr<RateErrorModel> em = CreateObject<RateErrorModel> ();
    em->SetAttribute ("ErrorRate", DoubleValue (0.00001));
    d1d3.Get(1)->SetAttribute ("ReceiveErrorModel", PointerValue (em));
    // Ptr<RateErrorModel> em2 = CreateObject<RateErrorModel> ();
    // em2->SetAttribute ("ErrorRate", DoubleValue (0.00001));
    d2d3.Get(1)->SetAttribute ("ReceiveErrorModel", PointerValue (em));

    InternetStackHelper internet;
    internet.Install (global);

    Ipv4AddressHelper ipv4;

    ipv4.SetBase ("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i1i3 = ipv4.Assign (d1d3);

    ipv4.SetBase ("10.2.2.0", "255.255.255.0");
    Ipv4InterfaceContainer i2i3 = ipv4.Assign (d2d3);                    

    Config::SetDefault("ns3::Ipv4GlobalRouting::RandomEcmpRouting",     BooleanValue(true)); // enable multi-path routing
    Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

    // n1 ----> n3 first link
    uint16_t TCPsinkPort = 8080;
    //TCP server/sink
    PacketSinkHelper packetSinkHelper ("ns3::TcpSocketFactory", InetSocketAddress(i1i3.GetAddress(1), TCPsinkPort));
    ApplicationContainer sinkApps = packetSinkHelper.Install (n3);
    sinkApps.Start (Seconds (0.));
    sinkApps.Stop (Seconds (30.)); 
    // TCP client
    TypeId tid = TypeId::LookupByName ("ns3::" + congestionControlAlgorithm);
    Config::Set ("/NodeList/*/$ns3::TcpL4Protocol/SocketType", TypeIdValue (tid));  
    Ptr<Socket> ns3TcpSocket = Socket::CreateSocket (n1, TcpSocketFactory::GetTypeId ());
    Ptr<MyApp> app = CreateObject<MyApp> ();
    app->Setup (ns3TcpSocket, InetSocketAddress( i1i3.GetAddress(1), TCPsinkPort), packetSize, 100000, DataRate (applicationDataRate)); 
    n1->AddApplication (app);
    app->SetStartTime (Seconds (1.));
    app->SetStopTime (Seconds (20.)); 

    AsciiTraceHelper asciiTraceHelper;
    Ptr<OutputStreamWrapper> stream = asciiTraceHelper.CreateFileStream ("connection-1-" +  congestionControlAlgorithm  + ".cwnd");
    ns3TcpSocket->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream));   

    // n1 ----> n3 second link
    TCPsinkPort = 8081 ; 
    // TCP server/sink
    PacketSinkHelper packetSinkHelper2("ns3::TcpSocketFactory", InetSocketAddress(i1i3.GetAddress(1), TCPsinkPort));
    ApplicationContainer sinkApps2 = packetSinkHelper2.Install (n3);
    sinkApps2.Start (Seconds (0.));
    sinkApps2.Stop (Seconds (30.));     
    // TCP client
    // TypeId tid = TypeId::LookupByName ("ns3::" + congestionControlAlgorithm);
    // Config::Set ("/NodeList/*/$ns3::TcpL4Protocol/SocketType", TypeIdValue (tid));  
    Ptr<Socket> ns3TcpSocket2 = Socket::CreateSocket (n1, TcpSocketFactory::GetTypeId ());
    Ptr<MyApp> app2 = CreateObject<MyApp> ();
    app2->Setup (ns3TcpSocket2, InetSocketAddress( i1i3.GetAddress(1), TCPsinkPort), packetSize, 100000, DataRate (applicationDataRate)); 
    n1->AddApplication (app2);
    app2->SetStartTime (Seconds (5.));
    app2->SetStopTime (Seconds (25.)); 

    AsciiTraceHelper asciiTraceHelper2;
    Ptr<OutputStreamWrapper> stream2 = asciiTraceHelper2.CreateFileStream ("connection-2-" +  congestionControlAlgorithm  + ".cwnd");
    ns3TcpSocket2->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream2));        
    
    
    // n2 ----> n3  link
    TCPsinkPort = 8082 ; 
    // TCP server/sink
    PacketSinkHelper packetSinkHelper3("ns3::TcpSocketFactory", InetSocketAddress(i2i3.GetAddress(1), TCPsinkPort));
    ApplicationContainer sinkApps3 = packetSinkHelper3.Install (n3);
    sinkApps3.Start (Seconds (0.));
    sinkApps3.Stop (Seconds (30.));     
    // TCP client
    // TypeId tid = TypeId::LookupByName ("ns3::" + congestionControlAlgorithm);
    // Config::Set ("/NodeList/*/$ns3::TcpL4Protocol/SocketType", TypeIdValue (tid));  
    Ptr<Socket> ns3TcpSocket3 = Socket::CreateSocket (n2, TcpSocketFactory::GetTypeId ());
    Ptr<MyApp> app3 = CreateObject<MyApp> ();
    app3->Setup (ns3TcpSocket3, InetSocketAddress( i2i3.GetAddress(1), TCPsinkPort), packetSize, 100000, DataRate (applicationDataRate)); 
    n2->AddApplication (app3);
    app3->SetStartTime (Seconds (15.));
    app3->SetStopTime (Seconds (30.)); 

    AsciiTraceHelper asciiTraceHelper3;
    Ptr<OutputStreamWrapper> stream3 = asciiTraceHelper3.CreateFileStream ("connection-3-" +  congestionControlAlgorithm  + ".cwnd");
    ns3TcpSocket3->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream3));     



    Simulator::Stop (Seconds (30));
    Simulator::Run ();
    Simulator::Destroy ();

    return 0;
}