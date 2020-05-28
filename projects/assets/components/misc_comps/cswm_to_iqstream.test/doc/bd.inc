  
\usetikzlibrary{shapes.geometric,arrows} % to implement the corresponding shapes and arrows, these are used.  
  
% the commands given below are used to define the styles for particular blocks. You can modify the dimensions, texture, etc. according to the requirements.  
   
\tikzstyle{block} = [rectangle, draw, fill=yellow!50,   
    text width=20.5em, text centered, rounded corners, minimum height=4em] % the width signifies the width of the box. You can change the width accordingly, while the height will be adjusted according to the text.  
    % it signifies that for the Block section, the Rectangle shape will be used. The color or shape can be modified.  
    % here, distance is the distance between the corresponding block  
\tikzstyle{line} = [draw, -latex']  
\tikzstyle{port} = [draw, ellipse,text width= 1em, fill=white!50, node distance=3cm, minimum height=1em]  
% the greater the value of the larger, the darker the color.  
% the shapes that are determined above with the width, and the color will only be used further. The shapes not declared here, will not be recognized by the Latex.     
 % the draw command here is used to draw the boundary of mentioned shape.  
% you can add more parameters to the tikzstyle according to the requirements.  
\begin{tikzpicture}[node distance = 1.8cm, auto] % the command node distance is important as it determines the space or the length of the arrow between different blocks.  
    % the command given below are the place of nodes  
    \node [port] (init) {in};  
    \node [block, below of= init](ProtocolADM){iqstream\_protocol De-marshalling};  
    \node [block, below of= ProtocolADM](ProtocolAdapt){Protocol Adaption};  
    \node [block, below of = ProtocolAdapt]({ProtocolBM}){ComplexShortWithMetadata Marshalling};  
    \node [port, below of = ProtocolBM](Out){out};    
    
    \path [line] (init) -- (ProtocolADM);   
    \path [line] (ProtocolADM) -- (ProtocolAdapt);   
    \path [line] (ProtocolAdapt) -- (ProtocolBM);   
    \path [line] (ProtocolBM) -- (Out);   
      
\end{tikzpicture} 
